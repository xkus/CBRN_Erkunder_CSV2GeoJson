import mgrs
import os
import csv
import geojson
import math
import shutil

path2Dir="RAD"  #Input
tmpDir="tmp"
geoDir="Output" #output
utmRef = mgrs.MGRS()

def utmDistance(pos1,pos2):    #Distanz funktion um Geschwindigkeit zu berechnen
    o1=int(pos1[5:10]) #32uvm igonieren und erste 5 Zahlen verwenden
    o2=int(pos2[5:10])
    n1=int(pos1[10:15])
    n2=int(pos2[10:15])
    diffO=abs(o1-o2)
    diffN=abs(n1-n2)
    return (math.sqrt((diffO*diffO)+(diffN*diffN)))

try:
    os.makedirs(tmpDir)   
except:
    pass
try:
    os.makedirs(geoDir)    
except:
    pass
    
# Verzeichnis auslesen und Kodierung aendern
for file in os.listdir(path2Dir):
    if not os.path.isdir(path2Dir + file):
        with open(path2Dir+'/'+file, 'r', encoding='windows-1250', errors='ignore') as infile:
            fileAtt=file.replace(".txt","")
            fileAtt=fileAtt.split("-")
            with open(tmpDir+'/'+fileAtt[0]+'-'+fileAtt[1].zfill(4)+'-'+fileAtt[2]+'-'+fileAtt[3]+'-'+fileAtt[4]+'-'+fileAtt[5]+'-'+fileAtt[6]+'.txt', 'w') as outfile:
                outfile.write(infile.read())
                
#Verzeichnis erneut  auslesen und Kommentar Dateien Suchen.
filedateOld=""
for file in sorted(os.listdir(tmpDir)):
    if not os.path.isdir(path2Dir + file):
        if file[0]==".":
            continue;
        fileAtt=file.replace(".txt","")
        fileAtt=fileAtt.split("-")
       # print(fileAtt)
        ###################
        #Abgesetzte Messung Einlesen
        if(fileAtt[6]=="RA(kom)"):
            try:
                datei = open(tmpDir+'/'+file,'r')
                x=0
                for zeile in datei:
                    if x==0:
                        zeile=zeile.split()
                        date=zeile[0]
                        time=zeile[1]
                    else:
                        if zeile.strip():
                            zeile=zeile.split(":")
                            if len(zeile)>1:
                                key=zeile[0].strip()
                                value=zeile[1].strip()
                               # print(value)
                                #print(key)
                                if key =="Beschreibung Startort":
                                        startPlace=value
                            else:
                                value=zeile[0].strip()
                    x=x+1
                #print(date)
                #print(time)
               # print(startPlace)
                measurement = csv.reader((open(tmpDir+'/'+fileAtt[0]+'-'+fileAtt[1]+'-'+fileAtt[2]+'-'+fileAtt[3]+'-'+fileAtt[4]+'-'+fileAtt[5]+'-RA(000).txt')), delimiter=";",quotechar='"')
                minV=1000
                maxV=0
                avr=0
                i=0
                for col in measurement:    
                    number=col[0]
                    date=col[1]
                    time=col[2]   
                    value =float(col[3].replace(",","."))
                    unit=col[4]   
                    avr=avr+value   
                    if value < minV:
                        minV=value
                    if value >maxV:
                        maxV=value
                    i=i+1
                avr=round(avr/i,3)
                point=geojson.Point(wsg84old)   
                Features.append(geojson.Feature(geometry=point, properties={"max": maxV,"avr": avr,"min": minV, "place":startPlace,"d_c":date,"t_c":time}))
            except Exception as e: 
                print(e)
               # print("Abgesetzte Messung nicht gefunden")
 ##########################################################################
 
###    RP= Online Messung Kommentar datei

########################################################################## 
        if(fileAtt[6]=="RP(kom)"):
            #kombiniere alle Messdaten von einem Tag in einer Datei. ohne IF wird fuer jeden gestartete Messung eine neue geojson angelegt.
            if not (filedateOld==fileAtt[0]):
               # print("new file")
                Coordinates=[]
                Features=[]       
            x=0
            #Schleife zum oeffnen der Daten dateien, beginnt bei ...RP(000).txt 
            for dataFileNumber in range(0,1000): 
                try:
                    #Daten Datei mit CSV und Tabulator lesen.
                    measurement = csv.reader((open(tmpDir+'/'+fileAtt[0]+'-'+fileAtt[1]+'-'+fileAtt[2]+'-'+fileAtt[3]+'-'+fileAtt[4]+'-'+fileAtt[5]+'-RP('+str(dataFileNumber).zfill(3)+').txt')), delimiter="\t",quotechar='"')
                    for col in measurement:
                        number=col[0]
                        date=col[1]
                        time=col[2]
                        utmCoordinates=col[4]
                        wsg84Temp=utmRef.toLatLon(utmCoordinates)
                        wsg84=[wsg84Temp[1],wsg84Temp[0]]
                        Coordinates.append(wsg84)
                        #print(wsg84)
                        idk=col[10]
                        idk2=col[11]
                        value1=float(col[12].lower())
                        unit1=col[13]
                        value2=float(col[14].lower())
                        unit2=col[15]
                       
                        #Fuer jede gelesene Zeile eine geojson Linie Zeichnen und Eigenschaften anhaengen.
                        #Linie hat nur einen Start und Endpunkt
                        if x >0:    
                            line=geojson.LineString([wsg84,wsg84old])   
                            v=round(utmDistance(utmCoordinates,utmCoordinatesOld)/(int(time)-int(timeOld))*3.6) # geschwindigkeit berchnen
                            if v <1 or v >150:      # wenn Auto steht oder bei GPS fehler, Zeile überspringen    
                                continue
                            #print(str(v))
                            Features.append(geojson.Feature(geometry=line, properties={"v1": value1,"v2":value2,"d":date,"t":time,"v":v})) #, "u1":unit1, "u2":unit2
                        x=x+1
                        wsg84old=wsg84 # Startpunkt fuer naechste Linie
                        utmCoordinatesOld=utmCoordinates
                        timeOld=time
                        
                except Exception as e: 
                       #print(e)
                         # keine weitere Daten Datei vorhanden. => geojson abspeichern
                        geojsonOutput=geojson.FeatureCollection(Features)
                        dump = geojson.dumps(geojsonOutput, sort_keys=True)
                        year="20"+fileAtt[0][0:2]
                        month=fileAtt[0][2:4]
                        day=fileAtt[0][4:6]
                        with open(geoDir+'/A0_'+year+'-'+month+'-'+day+'.geojson', 'w') as outfile:
                             outfile.write(dump)
                        #del wsg84old
                        break
            filedateOld=fileAtt[0]
shutil.rmtree(tmpDir,True)