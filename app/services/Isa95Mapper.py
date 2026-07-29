from pathlib import Path
import json
import restate
from pydantic import BaseModel, PositiveInt
from datetime import datetime

class Quantity(BaseModel):
    value: float
    unitOfMeasure: str

class EquipmentRequirement(BaseModel):
    id: str

class MaterialRequirement(BaseModel):
    id: str
    materialUse: str
    quantity: Quantity

class SegmentRequirement(BaseModel):
    id: str
    description: str
    equipmentRequirement: EquipmentRequirement
    duration: int
    materialRequirements: list[MaterialRequirement]

class HierarchyScope(BaseModel):
    id: str
    equipmentLevel: str

class OperationsRequest(BaseModel):
    id: str
    operationsType: str
    startTime: str
    endTime: str
    priority: PositiveInt
    hierarchyScope: HierarchyScope
    segmentRequirements: list[SegmentRequirement]

Isa95Mapper = restate.Service("Isa95Mapper")
@Isa95Mapper.handler("mapAndStore")

async def map_and_store(ctx: restate.Context, ERP:dict) -> dict:
    
    # validate that request only comes from validation service

    #only using get for the non-required fields 

    #operation request (OR)
    OR = {}
    OR["id"] = ERP["orderNumber"]
    OR["operationsType"] = ERP.get("operationsType","Production")
    OR["startTime"] = ERP["plannedStart"]
    OR["endTime"] = ERP["plannedEnd"]
    OR["priority"] = ERP.get("priority","")


    # Hierarchy Scope (HS)
    OR["hierarchyScope"] = {
        "id":ERP["plant"],
        "equipmentLevel":ERP.get("equipmentLevel","Site")
        }

    # Segment Requirements (SR)
    SRs = []
    for route in ERP["routing"]:
        sr={}

        sr["id"] = ERP["orderNumber"] + "-" + route["operation"]
        sr["description"] = route["description"]

        # "given in minutes" is unclear, would need clarification on whether they want int or float
        # maybe rounded to the nearest minute? Regardless, below just spits out whatever number, will likely be a float
        setup_mins = route["setupMinutes"] #is an int
        runs_min_per_unit = route["runMinutesPerUnit"]
        quantity = ERP["quantity"]
        sr["duration"] = setup_mins + (runs_min_per_unit * quantity) #paranthesis for clarity

        #equipmentRequirment
        sr["equipmentRequirement"] = {"id":route["workCenter"]}
        sr["materialRequirements"] = []

        SRs.append(sr)


    # Consumed Material
    #NTS: loop trhough components 
    CMs = []
    for component in ERP["components"]:
        consumed_material = {}
        
        consumed_material["id"] = component["materialNumber"]
        consumed_material["materialUse"] = "Consumed"
        consumed_material["quantity"] = {
            "value": component["quantityPer"] * ERP["quantity"],
            "unitOfMeasure": component["uom"]
        }

        CMs.append(consumed_material)

    SRs[0]["materialRequirements"].extend(CMs)

    # Produced Material
    #NTS: on the operation
    produced_material = {
        "id":ERP["material"]["materialNumber"],
        "materialUse":"Produced",
        "quantity": {
                "value":ERP["quantity"],
                "unitOfMeasure":ERP["material"]["uom"]
            }
    }

    #defining above makes the code more readable, but would be possible to compress it
    SRs[-1]["materialRequirements"].append(produced_material)

    OR["segmentRequirements"] = SRs


    operations_request =  {
        "operationsRequest":
        OperationsRequest.model_validate(OR).model_dump()
        }

    # save the json
    path = Path(f"output/{ERP['orderNumber']}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(operations_request, f, indent=4, default=str)

    return {"save_path":path.absolute().as_posix()}