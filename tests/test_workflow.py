import json
from unittest import IsolatedAsyncioTestCase
from typing import Tuple, Optional, Dict, Any
from libsimba_eth.workflow import (
    Action,
    ActionType,
    Workflow,
    DependencyType,
    Dependency,
    Contract,
    Executor,
)

initialize_name = "initialize"

initialize_abi = [
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "name",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "symbol",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "contractNamespace",
                "type": "string"
            },
            {
                "internalType": "address",
                "name": "admin",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "minter",
                "type": "address"
            },
            {
                "internalType": "address",
                "name": "pauser",
                "type": "address"
            },
            {
                "internalType": "uint256",
                "name": "maxSupply",
                "type": "uint256"
            }
        ],
        "name": "initialize",
        "outputs": [
        ],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

initialize_md = {
    "contract": {
        "methods": {
            "initialize": {
                "params": [
                    {
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "name": "symbol",
                        "type": "string"
                    },
                    {
                        "name": "contractNamespace",
                        "type": "string"
                    },
                    {
                        "name": "admin",
                        "type": "address"
                    },
                    {
                        "name": "minter",
                        "type": "address"
                    },
                    {
                        "name": "pauser",
                        "type": "address"
                    },
                    {
                        "name": "maxSupply",
                        "type": "uint256"
                    }
                ]
            }
        }
    }
}


class TestExecutor(Executor):
    count = 0

    async def deploy(
            self,
            workflow: Workflow,
    ) -> Workflow:
        self.count += 1
        return await super().deploy(workflow=workflow)

    async def deploy_library(
            self,
            org: str,
            lib_name: str,
            code: str,
            blockchain: str,
            app_name: str,
            encode: bool
    ) -> Tuple[Optional[Contract], Optional[str]]:
        if self.count == 1:
            return None, "could not deploy lib for some reason"
        contract = Contract(
            address=f"0x{self.count}",
            id=f"{self.count}",
            abi=[],
            metadata={}
        )
        return contract, None

    async def compile_contract(
            self,
            name: str,
            code: str,
            target_contract: str,
            libraries: Optional[Dict[str, str]] = None,
            encode: Optional[bool] = True
    ) -> Tuple[Optional[Contract], Optional[str]]:
        if self.count == 2:
            return None, "Could not compile design"
        if name == "SIMBAProxy":
            contract = Contract(
                design_id=f"{self.count}",
                abi=[],
                metadata={}
            )
        else:
            contract = Contract(
                design_id=f"{self.count}",
                abi=initialize_abi,
                metadata=initialize_md
            )
        return contract, None

    async def deploy_contract(
            self,
            contract: Contract,
            app_name: str,
            blockchain: str,
            storage: str,
            api_name: str,
            args: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Contract], Optional[str]]:
        if self.count == 3:
            return None, "Could not deploy contract"
        contract.address = f"0x{self.count}"
        contract.id = f"{self.count}"
        contract.api_name = api_name
        return contract, None

    async def submit_transaction(
            self,
            api_name: str,
            method: str,
            args: Optional[Dict[str, Any]] = None,
            wait: Optional[bool] = True
    ) -> Tuple[Optional[str], Optional[str]]:
        return f"0x{self.count}", None

    async def set_proxy(
        self,
        workflow: Workflow,
        proxy_contract: Contract,
        impl_contract: Contract,
    ) -> Tuple[Optional[str], Optional[str]]:
        return f"0x{self.count}", None


class TestWorkflow(IsolatedAsyncioTestCase):

    async def test_workflow(self):
        workflow = Workflow(
            org="MyOrg",
            app_name="myApp",
            blockchain="Quorum",
            actions=[
                Action(
                    contract_name="DataUri",
                    code="hello world",
                    action_type=ActionType.DEPLOY_LIBRARY,
                ),
                Action(
                    contract_name="Metadata",
                    code="hello world",
                    action_type=ActionType.DEPLOY_LIBRARY,
                ),
                Action(
                    contract_name="MyNft",
                    api_name="my-api",
                    code="hello world",
                    action_type=ActionType.DEPLOY_CONTRACT,
                    dependencies=[
                        Dependency(
                            parent="DataUri",
                            dependency_type=DependencyType.LIBRARY,
                        ),
                        Dependency(
                            parent="Metadata",
                            dependency_type=DependencyType.LIBRARY,
                        )
                    ]
                ),
                Action(
                    api_name="my-proxy",
                    action_type=ActionType.DEPLOY_PROXY,
                    dependencies=[
                        Dependency(
                            parent="MyNft",
                            dependency_type=DependencyType.IMPL,
                            method_name=initialize_name,
                            method_args={
                                "name": "My NFT",
                                "symbol": "MNT",
                                "contractNamespace": "com.simbachain",
                                "admin": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
                                "minter": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
                                "pauser": "0xa508dD875f10C33C52a8abb20E16fc68E981F186",
                                "maxSupply": 0
                            }
                        )
                    ]
                )
            ]
        )
        print(workflow.json(indent=2))
        print("==========")
        deployer = TestExecutor()
        workflow = await deployer.deploy(workflow=workflow)
        self.assertEqual(0, len(workflow.completed))
        self.assertEqual("FAILED_COMPLETE", workflow.actions[0].action_state)
        workflow = await deployer.deploy(workflow=workflow)
        print("*" * 20)
        print(workflow.json(indent=2))
        self.assertEqual(2, len(workflow.completed))
        self.assertEqual("0x2", workflow.completed.get("DataUri").contract.address)
        self.assertEqual("0x2", workflow.completed.get("Metadata").contract.address)
        self.assertEqual("FAILED_COMPILE", workflow.actions[0].action_state)
        workflow = await deployer.deploy(workflow=workflow)
        print("*" * 20)
        print(workflow.json(indent=2))
        self.assertEqual(2, len(workflow.completed))
        self.assertEqual("0x2", workflow.completed.get("DataUri").contract.address)
        self.assertEqual("0x2", workflow.completed.get("Metadata").contract.address)
        self.assertEqual("3", workflow.actions[0].contract.design_id)
        self.assertEqual("FAILED_COMPLETE", workflow.actions[0].action_state)
        workflow = await deployer.deploy(workflow=workflow)
        print("*" * 20)
        print(workflow.json(indent=2))
        self.assertEqual(4, len(workflow.completed))
        self.assertEqual("0x2", workflow.completed.get("DataUri").contract.address)
        self.assertEqual("0x2", workflow.completed.get("Metadata").contract.address)
        self.assertEqual("3", workflow.completed.get("MyNft").contract.design_id)
        self.assertEqual("0x4", workflow.completed.get("MyNft").contract.address)
        self.assertEqual("COMPLETED", workflow.completed.get("MyNft").action_state)
        self.assertEqual("4", workflow.completed.get("SIMBAProxy").contract.design_id)
        self.assertEqual("0x4", workflow.completed.get("SIMBAProxy").contract.address)
        self.assertEqual("COMPLETED", workflow.completed.get("SIMBAProxy").action_state)




