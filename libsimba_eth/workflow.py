import abc
import base64
import os

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from libsimba import Simba, simba_request
from pydantic import BaseModel, root_validator
from web3.auto import w3


class DependencyType(str, Enum):
    LIBRARY = "LIBRARY"
    CONSTRUCTOR = "CONSTRUCTOR"
    CONTRACT = "CONTRACT"
    IMPL = "IMPL"


class ActionType(str, Enum):
    DEPLOY_LIBRARY = "DEPLOY_LIBRARY"
    DEPLOY_CONTRACT = "DEPLOY_CONTRACT"
    METHOD_CALL = "METHOD_CALL"
    DEPLOY_PROXY = "DEPLOY_PROXY"


class ActionState(str, Enum):
    INITED = "INITED"
    COMPILED = "COMPILED"
    COMPLETED = "COMPLETED"
    FAILED_COMPILE = "FAILED_COMPILE"
    FAILED_COMPLETE = "FAILED_COMPLETE"
    FAILED_METHOD_CALL = "FAILED_METHOD_CALL"
    FAILED_SET_PROXY = "FAILED_SET_PROXY"
    FAILED_DEPENDENCIES = "FAILED_DEPENDENCIES"
    INVALID_STATE = "INVALID_STATE"


class Dependency(BaseModel):
    dependency_type: DependencyType
    parent: str
    # deployment arg to inject address into
    # if a constructor or method dependency
    target_arg: Optional[str] = None
    # impl method
    method_name: Optional[str] = None
    # impl method args
    method_args: Optional[Dict[str, Any]] = None


class Contract(BaseModel):
    id: Optional[str] = None
    address: Optional[str] = None
    api_name: Optional[str] = None
    design_id: Optional[str] = None
    abi: Optional[List[dict]] = None
    metadata: Optional[Dict[str, Any]] = None


class Action(BaseModel):
    action_type: ActionType
    # contract_name is optional because proxy name is loaded automatically
    contract_name: Optional[str] = None
    # code is optional because proxy code is loaded automatically
    code: Optional[str] = None
    dependencies: Optional[List[Dependency]] = None
    api_name: Optional[str] = None  # not needed for libraries
    args: Optional[Dict[str, Any]] = None
    action_state: Optional[ActionState] = ActionState.INITED
    contract: Optional[Contract] = None
    # for a proxy deployment this is the impl to wrap
    impl_contract: Optional[Contract] = None
    encode: Optional[bool] = True
    error_message: Optional[str] = None
    # if deployment type is METHOD_CALL or PROXY, this is the method name
    method_name: Optional[str] = None
    # used by contract deploy actions
    libraries: Optional[Dict[str, str]] = None

    @root_validator
    def check_by_type(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        action_type = values.get("action_type")
        if not action_type:
            raise ValueError("action type is required")
        if action_type == ActionType.DEPLOY_LIBRARY:
            cls.check_fields(
                action=action_type, values=values, fields=["contract_name", "code"]
            )
        elif action_type == ActionType.DEPLOY_CONTRACT:
            cls.check_fields(
                action=action_type,
                values=values,
                fields=["contract_name", "code", "api_name"],
            )
        elif action_type == ActionType.METHOD_CALL:
            cls.check_fields(
                action=action_type, values=values, fields=["method_name", "api_name"]
            )
        elif action_type == ActionType.DEPLOY_PROXY:
            cls.check_fields(action=action_type, values=values, fields=["api_name"])
        return values

    @classmethod
    def check_fields(
        cls, action: ActionType, values: Dict[str, Any], fields: List[str]
    ) -> None:
        for f in fields:
            if not values.get(f):
                raise ValueError(f" field {f} is required for action type {action}")


class Workflow(BaseModel):
    app_name: str
    org: str
    blockchain: str
    actions: List[Action]
    storage: Optional[str] = None
    completed: Dict[str, Action] = {}

    @root_validator
    def check(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        actions: List[Action] = values.get("actions")
        if not actions:
            raise ValueError("No actions defined.")
        previous: List[str] = []
        for i, action in enumerate(actions):
            if i == 0 and action.dependencies:
                raise ValueError("initial action cannot have dependencies")
            got_impl_dep = False
            if action.dependencies:
                for dep in action.dependencies:
                    if dep.parent and dep.parent not in previous:
                        raise ValueError(
                            "action depends on a action that is not defined previously"
                        )
                    if dep.dependency_type == DependencyType.IMPL:
                        got_impl_dep = True
            if action.action_type == ActionType.DEPLOY_PROXY and not got_impl_dep:
                raise ValueError(
                    "action is a deploy proxy but has not dependency on an impl"
                )


            previous.append(action.contract_name)
        return values


class Executor(abc.ABC):

    SIMBA_PROXY = "SIMBAProxy"

    async def handle_methodcall(
        self, action: Action, workflow: Workflow
    ) -> Tuple[Action, bool]:
        txn_id, err = await self.submit_transaction(
            api_name=action.contract.api_name,
            method=action.method_name,
            args=action.args,
        )
        if err:
            action.action_state = ActionState.FAILED_METHOD_CALL
            action.error_message = err
            return action, False
        action.action_state = ActionState.COMPLETED
        action.error_message = None
        return action, True

    async def handle_deploy_library(
        self, action: Action, workflow: Workflow
    ) -> Tuple[Action, bool]:
        # if it's not in a deployed state, then deployed contract should be null
        # if it's a library
        # library does compile and deploy in one
        contract = action.contract
        if contract:
            action.action_state = ActionState.INVALID_STATE
            action.error_message = "Contract already exists"
        contract, err = await self.deploy_library(
            org=workflow.org,
            lib_name=action.contract_name,
            code=action.code,
            blockchain=workflow.blockchain,
            app_name=workflow.app_name,
            encode=action.encode,
        )
        if err:
            action.action_state = ActionState.FAILED_COMPLETE
            action.error_message = err
            return action, False
        action.contract = contract
        action.action_state = ActionState.COMPLETED
        action.error_message = None
        return action, True

    async def handle_deploy_contract(
        self, action: Action, workflow: Workflow
    ) -> Tuple[Action, bool]:
        contract = action.contract
        if (
            not contract
            or not contract.design_id
            or action.action_state == ActionState.FAILED_COMPILE
        ):
            contract, err = await self.compile_contract(
                name=action.contract_name,
                code=action.code,
                target_contract=action.contract_name,
                libraries=action.libraries,
                encode=action.encode,
            )
            if err:
                action.action_state = ActionState.FAILED_COMPILE
                action.error_message = err
                return action, False
            action.contract = contract
            action.action_state = ActionState.COMPILED
            action.error_message = None
        contract, err = await self.deploy_contract(
            contract=contract,
            api_name=action.api_name,
            blockchain=workflow.blockchain,
            storage=workflow.storage,
            args=action.args,
            app_name=workflow.app_name,
        )
        if err:
            action.action_state = ActionState.FAILED_COMPLETE
            action.error_message = err
            action.error_message = None
            return action, False
        action.contract = contract
        action.action_state = ActionState.COMPLETED
        return action, True

    async def handle_deploy_proxy(
        self, action: Action, workflow: Workflow
    ) -> Tuple[Action, bool]:
        if action.action_state != ActionState.FAILED_SET_PROXY:
            # we're either on a first run, or we failed compile or deploy
            # so delegate to deploy contract
            action, carry_on = await self.handle_deploy_contract(
                action=action, workflow=workflow
            )
            if not carry_on:
                return action, False
        contract = action.contract
        msg, err = await self.set_proxy(
            workflow=workflow,
            proxy_contract=contract,
            impl_contract=action.impl_contract,
        )
        if err:
            action.action_state = ActionState.FAILED_SET_PROXY
            action.error_message = err
            return action, False
        return action, True

    @abc.abstractmethod
    async def deploy_library(
        self,
        org: str,
        lib_name: str,
        code: str,
        blockchain: str,
        app_name: str,
        encode: bool,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        """Go style return value and/or error"""
        ...

    @abc.abstractmethod
    async def compile_contract(
        self,
        name: str,
        code: str,
        target_contract: str,
        libraries: Optional[Dict[str, str]] = None,
        encode: Optional[bool] = True,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        """Go style return value and/or error"""
        ...

    @abc.abstractmethod
    async def deploy_contract(
        self,
        contract: Contract,
        app_name: str,
        blockchain: str,
        storage: str,
        api_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        """Go style return value and/or error"""
        ...

    @abc.abstractmethod
    async def submit_transaction(
        self,
        api_name: str,
        method: str,
        args: Optional[Dict[str, Any]] = None,
        wait: Optional[bool] = True,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Go style return value and/or error"""
        ...

    @abc.abstractmethod
    async def set_proxy(
        self,
        workflow: Workflow,
        proxy_contract: Contract,
        impl_contract: Contract,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Go style return value and/or error"""
        ...

    async def dependencies(
        self, action: Action, completed: Dict[str, Action]
    ) -> Tuple[bool, Optional[str]]:
        if ActionState.COMPLETED == action.action_state:
            # shouldn't happen as they are moved out when deployed
            return False, None
        dependencies = action.dependencies or []
        libs: Dict[str, str] = {}
        for dep in dependencies:
            dep_type = dep.dependency_type
            parent = dep.parent
            prev_deployment = completed.get(parent)
            if not prev_deployment:
                return False, f"Dependency on contract {parent} cannot be resolved"
            prev_contract = prev_deployment.contract
            if not prev_contract:
                return False, f"Dependency on contract {parent} cannot be resolved"
            if dep_type == DependencyType.LIBRARY:
                libs[parent] = prev_contract.address
            elif dep_type == DependencyType.CONSTRUCTOR:
                action.args[dep.target_arg] = prev_contract.address
            elif dep_type == DependencyType.CONTRACT:
                action.contract = prev_contract
            elif dep_type == DependencyType.IMPL:
                action.impl_contract = prev_contract
                action.code = self.load_proxy_encoded()
                action.encode = False
                action.contract_name = self.SIMBA_PROXY
                action.args = self.encode_calldata(
                    deployed_contract=action.impl_contract,
                    method_name=dep.method_name,
                    args=dep.method_args,
                )
            action.libraries = libs
        return True, None

    async def deploy(
        self,
        workflow: Workflow,
    ) -> Workflow:
        count = 0
        for i, action in enumerate(workflow.actions):
            carry_on, err = await self.dependencies(
                action=action, completed=workflow.completed
            )
            if err:
                action.action_state = ActionState.FAILED_DEPENDENCIES
                action.error_message = err
                break
            action.error_message = None
            if not carry_on:
                continue
            if action.action_type == ActionType.DEPLOY_LIBRARY:
                action, carry_on = await self.handle_deploy_library(
                    action=action, workflow=workflow
                )
                if not carry_on:
                    break
            elif action.action_type == ActionType.METHOD_CALL:
                action, carry_on = await self.handle_methodcall(
                    action=action, workflow=workflow
                )
                if not carry_on:
                    break
            elif action.action_type == ActionType.DEPLOY_CONTRACT:
                action, carry_on = await self.handle_deploy_contract(
                    action=action, workflow=workflow
                )
                if not carry_on:
                    break
            elif action.action_type == ActionType.DEPLOY_PROXY:
                action, carry_on = await self.handle_deploy_proxy(
                    action=action, workflow=workflow
                )
                if not carry_on:
                    break
            count += 1
            workflow.completed[action.contract_name] = action
        workflow.actions = workflow.actions[count:]
        return workflow

    def load_proxy_encoded(self) -> str:
        proxy_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "resources", "SIMBAProxy.sol"
        )
        with open(proxy_path) as proxy_file:
            return base64.b64encode(proxy_file.read().encode()).decode("utf-8")

    def encode_calldata(
        self, deployed_contract: Contract, method_name: str, args: Dict[str, Any]
    ):
        c = w3.eth.contract(abi=deployed_contract.abi)
        params = (
            deployed_contract.metadata.get("contract", {})
            .get("methods", {})
            .get(method_name, {})
            .get("params", [])
        )
        arg_list = []
        for param in params:
            arg_list.append(args.get(param.get("name")))
        encoded = c.encodeABI(fn_name=method_name, args=arg_list)
        return {"_logic": deployed_contract.address, "_data": encoded}


class SimbaExecutor(Executor):
    def __init__(self, simba: Simba):
        super().__init__()
        self.simba = simba

    async def deploy_library(
        self,
        org: str,
        lib_name: str,
        code: str,
        blockchain: str,
        app_name: str,
        encode: bool,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        path = f"/v2/organisations/{org}/deployed_artifacts/create/"
        if encode:
            code = base64.b64encode(code.encode()).decode("utf-8")
        full = {
            "lib_name": lib_name,
            "code": code,
            "language": "solidity",
            "blockchain": blockchain,
            "app_name": app_name,
        }
        poster = simba_request.PostRequest(endpoint=path)
        try:
            result: dict = await poster.post(json_payload=full)
            deployed_data = await self.simba.wait_for_deployment(org=org, uid=result.get("deployment_id"))
            print(deployed_data)
            data_address = SimbaExecutor.get_address(deployed_data, lib_name)
            contract = Contract(
                api_name=lib_name,
                address=data_address,
            )
            return contract, None
        except Exception as ex:
            return None, str(ex)

    @classmethod
    def get_address(cls, deployment, name):
        deps = deployment.get("deployment", [])
        primary = deployment.get("primary")
        print(f"primary: {primary}")
        if primary and primary.get("name") == name:
            return primary.get("address")
        for dep in deps:
            if dep.get("name") == name:
                return dep.get("address")
        return None

    async def compile_contract(
        self,
        name: str,
        code: str,
        target_contract: str,
        libraries: Optional[Dict[str, str]] = None,
        encode: Optional[bool] = True,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        pass

    async def deploy_contract(
        self,
        contract: Contract,
        app_name: str,
        blockchain: str,
        storage: str,
        api_name: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        pass

    async def submit_transaction(
        self,
        api_name: str,
        method: str,
        args: Optional[Dict[str, Any]] = None,
        wait: Optional[bool] = True,
    ) -> Tuple[Optional[str], Optional[str]]:
        pass

    async def set_proxy(
        self,
        workflow: Workflow,
        proxy_contract: Contract,
        impl_contract: Contract,
    ) -> Tuple[Optional[str], Optional[str]]:
        path = f"/v2/organisations/{workflow.org}/deployed_contracts/{proxy_contract.id}/proxy/"
        putter = simba_request.PutRequest(endpoint=path)
        try:
            result = await putter.put(json_payload={"implementation": impl_contract.id})
        except Exception as ex:
            return None, str(ex)
        return "OK", None
