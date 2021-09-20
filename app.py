# %%
#tkinter import
import tkinter as tk
from tkinter import StringVar, ttk
from threading import Thread

#important
import pandas as pd
import os
import json
import requests
import unidecode
import configparser
import datetime

# %%


exit_flag =False
def MockAthlete():
  MockVariable = [{
      "athlete":{
        "name":None,
        "surnames": None,
        "email":None,
        "birthday":None,
        "dni":None,
        "gender":None,
        "parentDni":None,
        "mobile":None,
      },

    "inscription": {
        "teamId": None,
        "club": None,
        "priceId": 0,
        "priceAmount": 0,
        "modalitySlug":None,
        "attributes": [],
        "paymentStatus": "PENDING",
      },
  }]
  return MockVariable
  
#translation 
translate = {
  "nombre":"name",
  "apellidos":"surnames",
  "numero_telefono":"mobile",
  "email":"email",
  "fecha_nacimiento":"birthday",
  "dni":"dni",
  "genero":"gender",
  "dni_pariente":"parentDni"
}


# %%script false --no-raise-error

from tkinter.constants import LEFT 
root=tk.Tk()
root.title('Automatizacion con Selenium y Python')
root.geometry('400x400')
varTotalState = StringVar()
varTotalState.set("0")
varTotalStateFail = StringVar()
varTotalStateFail.set("0")
varTotalStateOk = StringVar()
varTotalStateOk.set("0")
varTotalStateMessage = StringVar()
varTotalStateMessage.set("...")
varLen = StringVar()
varLen.set("0")



def threading():
    t1 = Thread(target=InscriptionButtonStart)
    t1.start()
# %%
def readExcel():
    excelPath = os.path.abspath("Excels")
    excel = pd.read_excel(excelPath + "/" + str(boxCombo.get()+".xlsx"),engine="openpyxl",dtype=str)
    return excel 

def lenExcel():
    lenghtExcel = len(readExcel())
    return lenghtExcel
#test  

def rowExcelData(number):
    dataRow = readExcel().loc[number]
    return dataRow

# %%

config = configparser.ConfigParser()
config.read("data.ini")
user = config.get("credentials","user")
password = config.get("credentials","password")


# %% 
credentialsBody = {"email": user, "password": password}


#### GET HEADER
def getHeader(includeToken = True):
        header = {"Content-Type": "application/json"}
        if includeToken:
            res = requests.post(backendUrl+"/auth",headers=header,data=json.dumps(credentialsBody)).json()
            token = res["token"]
            header["Authorization"] = "Bearer " + token
        return header

# %% Modality
def getIdModality():
    idModality = modalityUrl.rsplit('/',1)[1]
    return idModality
def getModalitySlug():
    res = requests.get(backendUrl + "/modality/"+ getIdModality(),headers= getHeader()).json()
    return res["slug"]
def getAtributes(idMod):
    res = requests.get(backendUrl + "/attributes/"+ str(idMod),headers=getHeader()).json()
    return res
# %% 
def cleanAttributes(idMod):
    res = getAtributes(idMod)["rows"]
    cleanAttributes = []
    for elem in res:
        array = {}
        array["id"] = elem["id"]
        array["type"] = elem["type"]
        array["name"] = unidecode.unidecode(" ".join(elem["name"].split()))
        array["options"] = []
        for attribute in elem["ModalityAttributesOptions"]:
            tmpArray = {}
            tmpArray["id"] = attribute["id"]
            tmpArray["name"] = unidecode.unidecode(attribute["name"]).lower()
            array["options"].append(tmpArray)
        cleanAttributes.append(array)
    return cleanAttributes
# %% 
def GetExtraModalityConfigInscription(price=False):
  returnarray = []
  res = requests.get(backendUrl + "/modality/" + getIdModality() + "/config_inscription",headers=getHeader()).json()
  if price == True:
    if(res["priceDefault"] == None):
        return 0 
    else:
        return res["priceDefault"]
  for element in list(res):
      if (res[element] == True and element not in ("allowInscriptions","priceDefault","selectClub")):
        returnarray.append(element)
  return returnarray
# %% 
def inscriptionDictCorrecting(modalityId,row):
    mockInscription  = MockAthlete()[0]["inscription"].copy()
    #price
    # we will get the price if 
    #modalitySlug
    mockInscription["modalitySlug"] = getModalitySlug()
    #atributes
    attributes = cleanAttributes(modalityId)
    currentExcelData = rowExcelData(row)
    
    for elem in attributes:
        mockInscription["attrs."+str(elem["id"])] = None
        for key,value in currentExcelData.items():
            if(key.lower() == "estado pago"):
                if(str(value).lower() != "nan"):
                    if(str(value).lower() == "pagado"):
                        mockInscription["paymentStatus"] = "PAID"
                    if(str(value).lower() == "pendiente"):
                        mockInscription["paymentStatus"] = "PENDING"
                    if(str(value).lower()=="denegado"):
                        mockInscription["paymentStatus"] = "DENIED"
                else:
                    mockInscription["paymentStatus"] = "PENDING"
            if(key.lower() == "precio"):
                if(str(value).lower() != "nan"):
                    mockInscription["priceAmount"] = int(value)
                else:
                    priceDefault = GetExtraModalityConfigInscription(True)
                    mockInscription["priceAmount"] = int(priceDefault)
            if(key.lower() == elem["name"]):
                for option in elem["options"]:
                    if(option["name"]== value.lower()):
                        mockInscription["attrs."+str(elem["id"])] = option["id"] 
                        mockInscription["attributes"].append({'id':elem["id"],'value':str(option["id"])})
    #attributes
    return mockInscription
# %% 
def addAditionalInfo():
    localDict ={}
    if GetExtraModalityConfigInscription():
        #check translation
        additional = GetExtraModalityConfigInscription()
        for key in additional:
            localDict[key] = None
    return localDict
# %% 
def translateExcel(row):
    #from Nombre to name
    current = rowExcelData(row)
    newDict = MockAthlete().copy()
    aditional = addAditionalInfo()
    for elem,key in aditional.items():
        newDict[0]["athlete"][elem] = None
    for key, value in current.items():
        if str(value) == "nan":
            current[key] = None
        ModifiedKey = key.lower()
        ModifiedKey = ModifiedKey.replace(" ","_")
        if(ModifiedKey in translate):
            newDict[0]["athlete"][translate[ModifiedKey]] = current[key]
            if(translate[ModifiedKey] == "gender"):
                if(value[0].lower() == "f"):
                    newDict[0]["athlete"][translate[ModifiedKey]] = "FEMALE"
                else:
                    newDict[0]["athlete"][translate[ModifiedKey]] = "MALE"
            if(translate[ModifiedKey]== "birthday"):
                newDict[0]["athlete"][translate[ModifiedKey]] = newDict[0]["athlete"][translate[ModifiedKey]].split(" ")[0]
    return newDict

# %%
def startScript(startRow = 0):
    try:
        currentModalityId = getIdModality()
        exitCount = lenExcel()
        for i in range (startRow,exitCount):
            athleteMod = translateExcel(i)
            athleteMod[0]["inscription"] = inscriptionDictCorrecting(currentModalityId,i)
            print(athleteMod)
            req = requests.post(backendUrl+ "/inscriptions", headers=getHeader(),data=json.dumps(athleteMod))
            if(req.status_code == 200):
                variableOk = varTotalStateOk.get()
                variableOk = int(variableOk)
                variableOk = variableOk +1 
                varTotalStateOk.set(str(variableOk))
            else:
                print(req.text)
                textWrite("Error en la fila: " + str(i+2) + " ---> "+ str(req.text))
                variableFail = varTotalStateFail.get()
                variableFail = int(variableFail)
                variableFail = variableFail +1 
                varTotalStateFail.set(str(variableFail))
        varTotalStateMessage.set("El programa acabo de realizar las inscripciones")
        textWrite("Resultado: Fallos: "+ varTotalStateFail.get() + "; Exito: " + varTotalStateOk.get() + "; Total: " + varTotalState.get())
    except Exception as e:
        print(e)


# %% 
modalityUrl = "tets"
backendUrl = "none"
def changeModalityUrlAndBackend():
    global modalityUrl
    global backendUrl
    modalityUrl = entry.get()
    if "gedsport" in modalityUrl:
            print("gedsport")
            backendUrl = config.get("url","backendPRO")
    else:
            print("not gedsport")
            backendUrl = config.get("url","backendPRE")
           
startRow = 0
def textWrite(text):
    with open('errores.txt', 'a') as the_file:
        the_file.write(
            text+ "\n")
def stop(self):
    self.stopped = True
# %% 
def InscriptionButtonStart():
    #change modalityURL
    changeModalityUrlAndBackend()
    varTotalStateFail.set("0")
    varTotalStateOk.set("0")
    varTotalState.set(str(lenExcel())) 
    textWrite(" ")
    textWrite("Modalidad: " + str(entry.get()))
    textWrite("Fecha: " + str(datetime.datetime.now()))
    
    
    #get configparser
    print(backendUrl)
    varTotalStateMessage.set("Haciendo las inscripciones...")
    startScript()
def ReturnExcelLenght():
    print("ok")
    varLen.set(str(lenExcel()))
    print(boxCombo.get())
    # change current url 

# %%script false --no-raise-error
# #Tkinter
excellist = [fname for fname in os.listdir("Excels")]
excellist = [f.split('.')[0] for f in excellist]
frameControls = tk.Frame(root)

entry = tk.Entry(root)
entry.grid(column=0,row=1,sticky='we',padx=5, pady=5)
tk.Label(root,text="Porfavor mete la url de la modalidad ",width=45).grid(column=0,row=0,sticky='w',columnspan=2,padx=5, pady=5)
boxCombo = ttk.Combobox(root,values=excellist)
boxCombo.grid(column=0,row=3,sticky='w',padx=5, pady=5)

tk.Label(root,text="Seleciona el excel",width=50,anchor="w").grid(column=0,row=2,sticky='we',padx=5, pady=5)
tk.Button(root,command=ReturnExcelLenght,text="Ver cuantas inscripciones estan en excel",bg="#02b5dd").grid(column=0,row=4,sticky='w',padx=5, pady=5)
tk.Label(root,textvariable=varLen).grid(column=1,row=4,sticky='w')


tk.Button(root,command=threading,text="Empezar",bg="#02b5dd").grid(column=0,row=7,sticky='w',padx=5, pady=5, columnspan=2)
tk.Label(root,text="Fallos",width=50,anchor="w").grid(column=0,row=8,sticky='we',padx=5, pady=5)
tk.Label(root,text="Exitos:",width=50,anchor="w").grid(column=0,row=9,sticky='we',padx=5, pady=5)
tk.Label(root,text="Total: ",width=50,anchor="w").grid(column=0,row=10,sticky='we',padx=5, pady=5)
tk.Label(root,textvariable=varTotalStateFail,width=50,anchor="w").grid(column=1,row=8,sticky='we',padx=5, pady=5)
tk.Label(root,textvariable=varTotalStateOk,width=50,anchor="w").grid(column=1,row=9,sticky='we',padx=5, pady=5)
tk.Label(root,textvariable=varTotalState,width=50,anchor="w").grid(column=1,row=10,sticky='we',padx=5, pady=5)
tk.Label(root,textvariable=varTotalStateMessage,width=50,anchor="w").grid(column=0,row=11,sticky='we',padx=5, pady=5)
root.mainloop()

