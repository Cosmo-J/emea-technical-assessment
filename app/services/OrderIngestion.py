import restate
from restate.exceptions import TerminalError
from datetime import datetime
from app.services.Isa95Mapper import map_and_store


OrderIngestion = restate.Service("OrderIngestion")


class dummy:
    def __init__(self) -> None:
        pass



class Validator:
    def __init__(self) -> None:
        self.errors = []

    # kwargs could define other validation steps that can be opted in for e.g. greater_than_0()
    # also additional logic needed to validate that datetime is in correct format
    # this logic also doesn't allow for multiple fail reasons

    #in hindsight, should really just use pydantic models instead of this custom class.
    def __call__(self,order_json,key,expected_type,positive=False,**kwargs):
        failed_reason = None

        if not isinstance(order_json,dict):
            value = dummy()
            failed_reason=f"Parent item missing for key {key}"
        else:
            value = order_json.get(key,dummy())

            if isinstance(value,dummy):
                failed_reason=f"Missing field: {key}"
            elif not isinstance(value,expected_type):
                failed_reason=f"Invalid type for key {key}. Expected {expected_type} and recieved {type(value)}"

        if positive and isinstance(value,(int,float)) and value<=0:
            print(value)
            failed_reason=f"{type(value)} must be greater than 0 (positive), for value of {key}, given value was {value}"

        if failed_reason:
            self.errors.append(failed_reason)
        return value


@OrderIngestion.handler("submitOrder")
async def submit_order(ctx: restate.Context, ERP:dict) -> dict:
    """ 
        1. recieves a submitted order
        2. Validates that order contains required fields
        3. Given valid, order sent to be parsed and mapped into ISA-95 with Isa95Mapper service
    """


    validate = Validator()

    #root
    validate(ERP,"orderNumber",str)
    validate(ERP,"plannedStart",str)
    validate(ERP,"plannedEnd",str)
    validate(ERP,"quantity",int,positive=True)
    validate(ERP,"plant",str)

    #material
    material_json = validate(ERP,"material",dict)

    validate(material_json,"materialNumber",str)
    validate(material_json,"uom",str)

    #routing operations
    routing_list = validate(ERP,"routing",list)

    if isinstance(routing_list,list):
        for r_json in routing_list:
            validate(r_json,"operation",str)
            validate(r_json,"workCenter",str)
            validate(r_json,"setupMinutes",int)
            validate(r_json,"runMinutesPerUnit",float)

    #components
    component_list = validate(ERP,"components",list)

    if isinstance(component_list,list):
        for r_json in component_list:
            validate(r_json,"materialNumber",str)
            validate(r_json,"quantityPer",float)
            validate(r_json,"uom",str)

    # used an LLM for code below because wasn't sure about best practise for returning failed processes (that shouldn't be retried) in the context of Restate
    # still unsure that its the best way to do it
    if validate.errors: 
        raise TerminalError(
            "Validation failed",
            status_code=400,
            metadata={
                f"error_{i + 1}": error
                for i,error in enumerate(validate.errors)
            }
        )


    mapped_order = await ctx.service_call(map_and_store, arg=ERP)
    return mapped_order