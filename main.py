from fastapi import FastAPI, Path ,Query
from pydantic import BaseModel , computed_field ,  Field
from fastapi.responses import JSONResponse
from typing import Literal, Annotated ,Optional
from fastapi import HTTPException
import json

app = FastAPI()

class Patient(BaseModel):
    name :   Annotated[str , Field(...,description="Name of patient",examples = ["Nikhil Yadav"],max_length=50)]
    city :   Annotated[str , Field(...,description="city of patient",examples = ["Mahenderagrh"],max_length=50)]
    age :    Annotated[int , Field(...,description="Name of patient",examples = [15,16,50],gt=0,lt=120)]
    gender : Annotated[Literal["male","female","other"] , Field(...,description="Gender of patient ")]
    height : Annotated[float , Field(...,description="height of patient in meters",examples = [1.67,1.72],gt=0,lt=3)]
    weight : Annotated[float , Field(...,description="weight of patient in kgs ",examples = [20,50,30.6,100.6],gt=0,lt=200)]
    
    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    @computed_field
    @property
    def verdict(self) -> str:

        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi < 25:
            return 'Normal'
        elif self.bmi < 30:
            return 'Overweight'
        else:
            return 'Obese'

class UpdatePatient(BaseModel):
    name :   Annotated[Optional[str], Field(default=None,description="Name of patient",examples = ["Nikhil Yadav"],max_length=50)]
    city :   Annotated[Optional[str] , Field(default=None,description="city of patient",examples = ["Mahenderagrh"],max_length=50)]
    age :    Annotated[Optional[int] , Field(default=None,description="Name of patient",examples = [15,16,50],gt=0,lt=120)]
    gender : Annotated[Optional[Literal["male","female","other"]] , Field(default=None,description="Gender of patient ")]
    height : Annotated[Optional[float] , Field(default=None,description="height of patient in meters",examples = [1.67,1.72],gt=0,lt=3)]
    weight : Annotated[Optional[float] , Field(default=None,description="weight of patient in kgs ",examples = [20,50,30.6,100.6],gt=0,lt=200)]
 

def load_patients():
    try:
        with open("patient.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="patient.json file not found"
        )
        
def patient_exists(patients: dict, new_patient) -> bool:
    for patient in patients.values():
        if (
            patient["name"] == new_patient.name
            and patient["age"] == new_patient.age
            and patient["city"] == new_patient.city
        ):
            return True

    return False

def generate_id(patients: dict) -> str:
    if not patients:
        return "P001"

    max_id = 0

    for patient_id in patients.keys():
        number = int(patient_id[1:])   # "P005" -> 5

        if number > max_id:
            max_id = number

    return f"P{max_id + 1:03d}"
        
def save_data(patients : dict) :
    with open("patient.json",'w') as f:
        json.dump(patients, f, indent=4)

@app.get("/")
def hello():
    return {"message" :"Pateint Managemnet System"}


@app.get("/about")
def about():
    return {"message":"A fully functional API to manage your Patients records "}


@app.get("/view")
def view():
    content = load_patients()
    return content 

@app.get("/patient/{patient_id}")
def view_patient(patient_id : str = Path(...,description="Id of the patient IN DB",examples=["P001"])):
    # load data 
    data = load_patients()
     
    patient = data.get(patient_id)
    
    if patient is None :
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )
    return patient

@app.get("/sort")
def sort_patient(sort_by : str = Query(...,description="sort on basis on height , weight or bmi (not case sensitive)"),
                 order : str = Query("asc",description="sort in asc or desc order (not case sensitive)")):
    valid_fields = ["height","weight","bmi"]
    orders = ["asc","desc"]
    if sort_by.lower() not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail= f"Invalid Sort Field :  select from {valid_fields}"
        )
        
    if order.lower() not in orders:
            raise HTTPException(
            status_code=400,
            detail= f"Invalid Order  Field :  sel ect from {orders }"
        )
            
    #load data 
    data = load_patients()
    
    sort_order = True if order == "desc" else False
    
    sorted_data = sorted(data.items(),key = lambda X : X[1].get(sort_by.lower(),0),reverse=sort_order)
    
    return sorted_data


@app.post("/create")
def create(new_patient : Patient):
    
    # load data 
    patients = load_patients()
    
    # id generator 
    new_id = generate_id(patients)
    # check if already exists

    if patient_exists(patients, new_patient):
        raise HTTPException(
            status_code=409,
            detail="Patient already exists."
        )
    # new patient added 
    patients[new_id] = new_patient.model_dump()
    
    save_data(patients)
    return JSONResponse(status_code=201, content={'message':'patient created successfully'})

@app.put("/update/{patient_id}")
def update_patient(patient_update: UpdatePatient,
                   patient_id: str = Path(...,description="Id of the patient IN DB",examples=["P001"])):
    
    # load data 
    data = load_patients()
    
    if patient_id not in data:
        raise HTTPException(status_code=404,
    detail="Patient not found")
        
    existing_patient_info = data.get(patient_id)
    # model change dictionary
    updated_patient_info = patient_update.model_dump(exclude_unset=True)
    
    #update the values 
    for key , value in updated_patient_info.items():
        existing_patient_info[key] = value
    
    
    # retrriger the Patient model to update the computed fields    
    patient_pydantic_obj = Patient(**existing_patient_info)
    existing_patient_info  = patient_pydantic_obj.model_dump()
    
    #actual updating 
    data[patient_id] = existing_patient_info
    
    #saving data in json file 
    save_data(data)
    
    return JSONResponse(status_code=200,content={"message":"patient updated"})

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id:str):
    # laod data 
    data = load_patients()
    
    # check if patient exists or not
    if patient_id not in data:
        raise HTTPException(status_code=404,detail="Patient not found")
    #delete information 
    del data[patient_id]
    
    #save data 
    save_data(data)
    
    return JSONResponse(status_code=200, content={'message':'patient deleted'})
