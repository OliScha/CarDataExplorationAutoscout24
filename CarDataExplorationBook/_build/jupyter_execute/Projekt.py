#!/usr/bin/env python
# coding: utf-8

# # Project

# In diesem Projekt wird eine Explorative Datenanalyse von Automobilen durchgeführt. <br>
# Als Datengrundlage dient die Webseite Autoscout24 (https://www.autoscout24.de/), eine Online-Plattform zum Kauf und Verkauf von Neu- und Gebrauchtwagen. <br>
# ![Autoscout24 Startseite](/Autoscout24.png) <br>
# ![Autoscout24 Suche](/Autoscout24Suche.png) <br>
# Ziel ist es, die Daten verschiedener Fahrzeuge zu vergleichen und daraus mögliche Schlüsse auf Korrelation der Daten zu ziehen. So soll beispielsweise analysiert werden, welche Fahrzeugeigentschaften einen Einfluss auf dessen Verkaufspreis haben. <br>
# Eine weitere interessante Fragestellung ist der Zusammenhang zwischen Kraftstoffart und Verbrauchsdaten. <br>
# Die im Projekt getätigten Analysen und Vergleiche verschiedener Fahrzeuge sollen zudem als Kaufentscheidung eines Fahrzeugs dienen. 

# ## Import

# Zunächst wreden alle für dieses Projekt benötigten Packages und Bibliothen importiert.

# In[1]:


#Basics
import pandas as pd
import numpy as np

#Webcrawling
#pip install beautifulsoup4
from bs4 import BeautifulSoup
import requests

#Deactivate warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# In[2]:


#Data visualization
import matplotlib.pyplot as plt

import plotly.express as px
import plotly.graph_objs as go
import plotly.io as pio
import plotly.figure_factory as ff
import plotly.offline as pyo
# Set notebook mode to work in offline
pyo.init_notebook_mode()

#np.set_printoptions(precision=6)
#np.set_printoptions(suppress=True)

import seaborn as sns 


# In[3]:


#Geo visualization
import folium
#!pip install geopy
from geopy.geocoders import Nominatim


# ## Webcrawling & Creation of Dataframe

# Als Erstes ist es notwendig, die Fahrzeugdaten von der Webseite Autoscout24 zu crawlen und in einem Dataframe zu speichern. 
# 
# Für das Crawlen der Daten wird die Methode *extractPageCarDF* definiert. Dieser muss beim Aufruf die Variable *URL* mitgegeben werden. Dabei handelt es sich um den Link zu einem Autoscout24 Suchergebnis, welches stehts 20 Autos beinhaltet (sofern sie den Suchkriterien entsprechen). <br>
# Jedes Auto wird dabei vom HTML Element *Article* umschlossen. Daher wird eine Schleife implementiert, welche für jedes Auto im Suchergebnis die nachfolgenden Daten aus den dazugehörigen HTML Elementen der Webseite extrahiert: <br>
# * Titel
# * Fahrzeugversion
# * Untertitel
# * Preis
# * Leasingpreis
# * Fahrzeugstandort
# 
# Falls eines der HTML-Elemente nicht gefunden werden kann, wird jede der Anweisungen durch einen try except Block umschlossen. Falls kein Eintrag gefunden wird, wird der jeweilige Wert mit einem NULL-Wert belegt.
# 
# Eine Besonderheit ist zudem der Preis. Wird das Element *ListItem_pricerow* gefunden, handelt es sich um einen Verkaufspreis und kein Leasingangebot. *Leasing* wird daher False gesetzt. Wird dieses Element nicht gefunden, sondern *LeasingPrice_price* handelt es sich um ein Leasing Angebot.
# 
# Diese Daten werden dem Dataframe *pageCarDF* hinzugefügt. 
# 
# In einer weiteren Schleife werden die folgenden Fahrzeugdetaildaten aus dem HTML Div Container *VehicleDetailTable* abgezogen: <br>
# ![Autoscout24 VehicleDetailTable](/VehicleDetailTable.png) <br>
# Es wird zunächst ein leeres Dataframe initialisiert.
# In einer Schleife wird für jedes Fahrzeug die leere Liste *VehicleDetailList* erzeugt und dieser in einer inneren Schleife jedes Element der *VehicleDetailTable* hinzugefügt. <br>
# Die Liste wird anschließend dem *VehicleDetailDF* hinzugefügt. Hierfür ist ein try except notwendig. Leasing Fahrzeuge haben ein zweites Element namens *VehicleDetailTable*, welches allerdings nur 3 Einträge zum Themengebiet Leasing hat. Der Versuch diese Listen mit 3 Einträgen dem *VehicleDetailDF* hinzuzufügen, läuft aufgrund nicht passender Längen auf Fehler. Dieser Fehler wird im except Block bewusst mit einem Continue abgefangen. Die Leasing *VehicleDetailLists* werden nicht weiter benötigt und fallen somit raus. <br>
# 
# Nun liegt das *pageCarDF* und das *VehicleDetailDF* vor, welche beide je Fahrzeug eine Zeile beinhalten.<br>
# Die beiden Dataframes werden mithilfe der merge-Methode über den Index gejoined. <br>
# 
# Die Methode gibt das Dataframe *pageCarDF* als return value zurück. Diese beinhaltet alle relevanten Daten von den Fahrzeugen einer Suchergebnisseite (in der Regel 20 Fahrzeuge).

# In[4]:


def extractPageCarDF(URL):

    soup=BeautifulSoup(requests.get(URL).text,"html.parser")
    pageCarDF=pd.DataFrame()

    for car in soup.findAll("article"):
        data = car.find("div", {"class": lambda L: L and L.startswith("ListItem_wrapper")})
        try:
            header = data.find("h2").text
        except:
            header = np.NaN
        try:
            version = data.find("span", {"class": lambda L: L and L.startswith("ListItem_version")}).text
        except:
            version = np.NaN
        try:
            subtitle = data.find("span", {"class": lambda L: L and L.startswith("ListItem_subtitle")}).text
        except:
            subtitle = np.NaN
        try:
            #Versuch Preis Element zu finden
            price = data.find("div", {"class": lambda L: L and L.startswith("ListItem_pricerow")}).text
            leasing = False
        except:
            #wenn oberes Element nicht gefunden werden kann, handelt es sich um einen Leasing Wagen, mit dem nachfolgenden HTML Element
            price = data.find("span", {"class": lambda L: L and L.startswith("LeasingPrice_price")}).text
            leasing = True 

        try:
            location = car.find("span", {"style": lambda L: L and L.startswith("grid-area:address")}).text
        except:
            location = np.NaN

        #Daten dem pageCarDF hinzufügen
        pageCarDF = pageCarDF.append({"Titel":header, "Version":version, "Untertitel":subtitle, "Preis":price, "Leasing":leasing, "Standort":location}, ignore_index=True)


    #VehicleDetailTable
    VehicleDetailDF = pd.DataFrame()
    for car in soup.findAll("div" , {"class":"VehicleDetailTable_container__mUUbY"}):
        VehicleDetailList = []
        for c in car:
            VehicleDetailList.append(c.text)
        try:
            VehicleDetailDF = VehicleDetailDF.append({"km":VehicleDetailList[0], "Erstzulassung":VehicleDetailList[1], "PS":VehicleDetailList[2], "Zustand":VehicleDetailList[3], "Fahrzeughalter":VehicleDetailList[4], "Getriebe":VehicleDetailList[5], "Kraftstoff": VehicleDetailList[6], "Verbrauch_l_pro_100km":VehicleDetailList[7], "Emissionen_g_pro_km":VehicleDetailList[8]}, ignore_index=True)
        except:
            continue #VehicleDetailLists mit Länge 3 sind extra VehicleDetailTables, die nur bei Leasing Wagen vorkommen. Diese sollen nicht übernommen werden, daher Continue
    
    #Join pageCarDF und VehicleDetailDF
    pageCarDF = pd.merge(pageCarDF, VehicleDetailDF, left_index=True, right_index=True)   

    return pageCarDF


# Die Methode *extractPageCarDF* gilt es nun mit den passenden Paramentern aufzurufen. 
# 
# Es werden zunächst zwei leere Dataframes initialisiert. <br>
# Die Suche auf Autoscout24 wurde zunächst komplett ohne Filter aufgerufen. Pro Suchergebnis gibt die Webseite ingesamt 20 Suchergebnisseiten mit jeweils 20 Fahrzeugen aus. Somit können mit einer Suche maximal 20 * 20 = 400 Autos von der Webseite gecrawlt werden. <br>
# Da für die Analysen im Projekt mehr als 400 Datensätze gewünscht sind, wird ein Filter "Erstzulassung bis" gesetzt. Die Jahreszahlen werden in der Liste *fregtoList* von 1990 bis 2022 in 2er Schritten gewählt.
# 
# In einer Schleife wird zunächst der Filter auf die jeweilige Jahreszahl gesetzt. In einer inneren Schleife werden jeweils die 20 Seiten des Suchergebnisses gecrawlt. <br>
# Dafür wird zunächst die URL aus "Erstzulassung bis" *fregto=* und Suchergebnisseite *page* erstellt. Die URL wird an die Methode *extractPageCarDF* übergeben und diese ausgeführt. <br>
# Das resultierende Dataframe *pageCarDF* mit 20 Einträgen wird dem Dataframe *AutoDFraw* angehängt. Anschließend wird die Methode für die nächste Seite um Suchergebnis ausgeführt und das Ergebnis wieder *AutoDFraw* hinzufügt. <br>
# Dataframe *pageCarDF* wird somit bei jeder Ausführung der Methode *extractPageCarDF* neu erstellt, während Dataframe *AutoDFraw* immer weiter wächst. 
# 
# Die Methode wird für jeden Filter "Erstzulassung bis" für 20 Suchergebnisseiten ausgeführt, sodass das Dataframe *AutoDFraw* am Ende über 6000 Einträge enhält.

# In[5]:


AutoDFraw=pd.DataFrame()
pageCarDF=pd.DataFrame()
baselink = "https://www.autoscout24.de/lst?fregto="
fregtoList = list(range(1995, 2022, 1))
#fregfromList = list(range(1991, 2021, 2))
#fregfromList.insert(0, 1900)

for freg in fregtoList:
    for page in range(20):
        URL = baselink + str(freg) + "&page=" + str(page)
        pageCarDF = extractPageCarDF(URL)
        AutoDFraw=pd.concat([AutoDFraw, pageCarDF],axis=0, ignore_index=True)


# In[58]:


AutoDFraw


# ## Raw Data Transformation

# Die Fahrzeugdaten von Autoscout24 wurden erfolgreich abgezogen und in einem Dataframe gespeichert. Allerdings entsprechen viele Spalten noch nicht dem gewünschten Format, da beispielsweise Sonderzeichen enthalten sind oder numerische Werte nicht also solche erkannt werden. <br>
# Aus diesem Grund muss das Dataframe nun so bearbeitet werden, dass alle Spalten in einer für die Explorative Datenanalyse sinnvollen Struktur vorliegen.

# Zunächst werden die Rohdaten in einer Excel Tabelle gespeichert. So kann jederzeit auf die Rohdaten zurückgegriffen werden und auch das Ergebnis der Datentransformation nachvollzogen werden.

# In[59]:


AutoDFraw.to_excel("AutoDF_vor_Replace.xlsx")


# Anschließend wird das Dataframe *AutoDF* mit den Rohdaten initialisiert.

# In[62]:


AutoDF= AutoDFraw


# Eine für die Datenanalyse interessante Information ist die Automarke. Diese ist im Titel der Anzeige als erstes Wort enthalten. Daher wird zur Bestimmung der Automarke das erste Wort der Spalte *Titel* extrahiert und in einer neuen Spalte *Marke* gespeichert.

# In[63]:


AutoDF['Marke'] = AutoDF['Titel'].str.split('\s+').str[0]


# Im nächsten Schritt wird das Dataframe um störende oder überflüssige Character bereinigt. Dazu gehören störende Satzzeichen, Währungen, Strings, etc. 
# 
# Da in einzelnen Fällen Leasingpreise noch hinter Kaufpreisen angezeigt werden, müssen zuerst alle Zeichen hinter dem ersten Kaufpreis entfernt werden.  Dann werden in der nächsten Codezeile alle weiteren nicht numerischen Zeichen entfernt.

# In[64]:


AutoDF['Preis'] = AutoDF['Preis'].replace('(,-).*', '',regex=True)
AutoDF['Preis'] = AutoDF['Preis'].str.replace(r'[^0-9]+', '')


# Die nachfolgenden Spalten enthalten im Datensatz noch Einheiten. Diese sind bereits im Spaltentitel vorhanden und werden somit aus den Datensätzen entfernt, sodass nur noch numerische Werte verbleiben.

# In[65]:


AutoDF['km'] = AutoDF['km'].replace(r'[^0-9]+', '',regex=True)
AutoDF['Fahrzeughalter'] = AutoDF['Fahrzeughalter'].replace(r'[^0-9]+', '',regex=True)
AutoDF['Verbrauch_l_pro_100km'] = AutoDF['Verbrauch_l_pro_100km'].replace(['\(l/100 km\)', 'l/100 km','\(komb.\)'], '',regex=True)
AutoDF['Emissionen_g_pro_km'] = AutoDF['Emissionen_g_pro_km'].replace(r'[^0-9]+', '',regex=True)


# Der Monat der Erstzulassung wird entfernt sowie alle übrigbleibenden nicht numerischen Zeichen.

# In[66]:


AutoDF['Erstzulassung'] = AutoDF['Erstzulassung'].replace('.*/', '',regex=True)
AutoDF['Erstzulassung'] = AutoDF['Erstzulassung'].replace(r'[^0-9]+', '',regex=True)


# Bei der PS-Angabe  muss zuerst der Wert in kW entfernt werden, danach alle weiteren nicht numerischen Zeichen.

# In[67]:


AutoDF['PS'] = AutoDF['PS'].replace(['.*kW','\(','PS\)'], '',regex=True)
AutoDF['PS'] = AutoDF['PS'].replace(r'[^0-9]+', '',regex=True)


# # Oli check hier den Text nochmal bitte

# Bei der Bereinigung fehlender Werte tritt das Problem auf, dass bei den Attributen *Verbrauch* und *Emissionen* fehlende Werte bei Elektroautos = 0 bedeuten, bei nicht Elektroautos jedoch tatsächlich fehlende Werte.
# 
# Da bei Verbrauch und Emissionen von Nutzern teilweise keine Werte angegeben werden, werden alle fehlenden Werte durch NULL ersetzt, 
# damit diese später ausgewertet werden können.

# In[68]:


AutoDF['Verbrauch_l_pro_100km'] = AutoDF['Verbrauch_l_pro_100km'].replace(['-','','0'], np.NaN,regex=True)
AutoDF['Emissionen_g_pro_km'] = AutoDF['Emissionen_g_pro_km'].replace(['-','','0'], np.NaN,regex=True)
AutoDF['Fahrzeughalter'] = AutoDF['Fahrzeughalter'].replace(['-',''], np.NaN,regex=True)
AutoDF['Erstzulassung'] = AutoDF['Erstzulassung'].replace('', np.NaN,regex=True)
AutoDF['km'] = AutoDF['km'].replace('', np.NaN,regex=True)
AutoDF['PS'] = AutoDF['PS'].replace('', np.NaN,regex=True)

# da keine Angabe bei Verbrauch und Emissionen bei Elektroautos korrekt sein kann, wird der Wert wieder durch 0 ersetzt
AutoDF.loc[AutoDF.Kraftstoff == 'Elektro', 'Verbrauch_l_pro_100km'] = 0
AutoDF.loc[AutoDF.Kraftstoff == 'Elektro', 'Emissionen_g_pro_km'] = 0

AutoDF


# In der spalte *Verbrauch_l_pro_100km* wird das Komma zur Dezimaltrennung durch einen Punkt ersetzt.

# In[70]:


AutoDF['Verbrauch_l_pro_100km'] = AutoDF['Verbrauch_l_pro_100km'].replace(',', '.',regex=True)


# Die Spalte *Standort* wird aufgeteilt in die Spalten *PLZ*, *Stadt* und *Land*. <br>
# Das letzte Wort der Spalte *Standort* ist immer der Stadtname. <br>
# Die Postleitzahl kann extrahiert werden, indem alle nicht numerischen Zeichen entfernt werden. <br>
# Land und PLZ werden durch einen Bindestrich getrennt. Daher kann der Bindestrich zum Split verwendet werden, wobei der erste Teil weiterverwendet wird. Dieser wird nochmal mit durch Leerzeichen getrennt und hiervon der letzte Teil als *Land* gespeichert.

# In[71]:


#Stadtname
AutoDF['Stadt'] = AutoDF['Standort'].str.split(' ').str[-1]

#PLZ
AutoDF['PLZ'] = AutoDF['Standort'].replace(r'[^0-9]+', '',regex=True)

#Land
AutoDF['Land'] = AutoDF['Standort'].str.split('-').str[-2].str.split(' ').str[-1]

AutoDF


# Spalte Standort wird nicht weiter benötigt und kann entfernt werden.

# In[72]:


AutoDF = AutoDF.drop('Standort', axis=1)


# In der Spalte *Untertitel* werden Ausstattungsmerkmale des Fahrzeugs aufgezählt. Einige ausgewählte Austattungsmerkmale werden als extra Spalten in das Dataframe aufgenommen. <br>
# Dafür wird folgende Annahme getroffen: <br> 
# Ein Fahrzeug besitzt eine bestimmte Ausstattung, wenn diese in Spalte *Untertitel* erwähnt wird. Wird diese dort nicht erwähnt, besitzt ein Fahrzeug diese Ausstattung nicht. <br>
# Dies wird mithilfe der Methode str.contains geprüft.

# In[73]:


AutoDF['Alufelgen']= AutoDF['Untertitel'].str.contains("Alufelgen")
AutoDF['Sitzheizung']= AutoDF['Untertitel'].str.contains("Sitzheizung")
AutoDF['Klimaanlage']= (AutoDF['Untertitel'].str.contains("Klimaanlage")) | (AutoDF['Untertitel'].str.contains("Klimaautomatik"))
AutoDF['Einparkhilfe']= AutoDF['Untertitel'].str.contains("Einparkhilfe ")
AutoDF['Navigationssystem']= AutoDF['Untertitel'].str.contains("Navigationssystem")
AutoDF


# Abgesehen von *Klimaanlage* entstehen None Values in den neu erzeugten Ausstattungsspalten wenn die Spalte *Untertitel* None ist, daher werden diese nun durch False ersetzt.
# Dafür wird davon ausgegangen, dass ein Fahrzeug bspw. keine Alufelgen hat, wenn keine Beschreibung unter *Untertitel* angegeben ist.

# In[74]:


AutoDF['Alufelgen'] = AutoDF['Alufelgen'].replace(np.NaN, False)
AutoDF['Sitzheizung'] = AutoDF['Sitzheizung'].replace(np.NaN, False)
AutoDF['Einparkhilfe'] = AutoDF['Einparkhilfe'].replace(np.NaN, False)
AutoDF['Navigationssystem'] = AutoDF['Navigationssystem'].replace(np.NaN, False)
AutoDF


# In der Spalte *Leasing* werden die Werte noch mit 0.0 für False und 1.0 für True ausgegeben. Dies wird in Boolean Werte geändert.

# In[75]:


AutoDF['Leasing'] = AutoDF['Leasing'].replace(0.0, False)
AutoDF['Leasing'] = AutoDF['Leasing'].replace(1.0, True)


# Mit der .info() Methode werden nun alle Spalten des Dataframes mit deren Datentypen angezeigt.

# In[76]:


AutoDF.info()


# Das Dataframe hat 22 Spalten. Davon haben die meisten den Datentyp *object*, obwohl es sich bei einigen davon um numerische Werte handelt. Dies muss noch geändert werden. Lediglich die Boolean Spalten wie beispielsweise *Leasing* wurden korrekt identifiziert. <br>
# Die meisten Spalten haben keine NULL Werte. Allerdings exisitieren auch Spalten, die sehr viele NULL-Werte aufweisen. Beispielsweise *Emissionen_g_pro_km*. <br>
# Nachfolgend werden die NULL-Werte in einer heatmap visuaisiert.

# In[77]:


sns.set_theme(style="ticks", color_codes=True)

# Identifizieren der NULL Werte via Heatmap
sns.heatmap(AutoDF.isnull(), 
            yticklabels=False,
            cbar=False, 
            cmap='viridis');


# In der Heatmap ist zu erkennen, dass sehr viele NULL-Werte in den Spalten *Untertitel*, *Fahrzeughalter*, *Verbrauch_l_pro_100km* und *Emissionen_g_pro_km* exisitieren. <br>
# Nachfolgend werden hierfür nochmal die exakten Mengen ausgegeben:

# In[78]:


print(AutoDF.isnull().sum())


# Die Spalten *Verbrauch_l_pro_100km* und *Emissionen_g_pro_km* weisen viele NULL-Werte auf. Für die Analyse sind diese jedoch von großer Bedeutung. Zeilen mit fehlenden Abgas- oder Verbrauchswerten bzw. fehlenden Kilometer und PS-Angaben werden daher gelöscht.
# # noch mehr Begründung, warum wir Null Werte löschen?
# 

# In[79]:


AutoDF = AutoDF[AutoDF['Verbrauch_l_pro_100km'].notna()]
AutoDF = AutoDF[AutoDF['Emissionen_g_pro_km'].notna()]
AutoDF = AutoDF[AutoDF['km'].notna()]
AutoDF = AutoDF[AutoDF['PS'].notna()]
print(AutoDF.isnull().sum())


# Als nächstes werden die Datentypen angepasst, indem numerische Spalten einer Datentypkonvertierung unterzogen werden.

# In[80]:


AutoDF['Preis'] = AutoDF['Preis'].astype('int')
AutoDF['km'] = AutoDF['km'].astype('int')
AutoDF['PS'] = AutoDF['PS'].astype('int')
AutoDF['Emissionen_g_pro_km'] = AutoDF['Emissionen_g_pro_km'].astype('int')
AutoDF['Erstzulassung'] = AutoDF['Erstzulassung'].astype('float')
AutoDF['Verbrauch_l_pro_100km'] = AutoDF['Verbrauch_l_pro_100km'].astype('float')


# Die Spalten *Zustand*, *Getriebe*, *Kraftstoff* *Marke* und *Land* weisen jeweils nur eine geringe Menge verschiedener Ausprägungen vor. Daher werden diese Spalten im Typ categorical abgespeichert. Alle übrigen Spalten verbleiben als object.

# In[81]:


AutoDF['Zustand'] = AutoDF['Zustand'].astype('category')
AutoDF['Getriebe'] = AutoDF['Getriebe'].astype('category')
AutoDF['Kraftstoff'] = AutoDF['Kraftstoff'].astype('category')
AutoDF['Marke'] = AutoDF['Marke'].astype('category')
AutoDF['Land'] = AutoDF['Land'].astype('category')


# In[82]:


AutoDF.info()


# ## Descriptive Statistics

# Nachfolgend werden alle numerischen Features in einer Liste gespeichert.

# In[83]:


num_features=AutoDF.select_dtypes(include=np.number).columns.to_list()
num_features


# Gleiches wird für alle nicht numerischen Features durchgeführt.

# In[84]:


cat_features=AutoDF.select_dtypes(exclude=np.number).columns.to_list()
cat_features


# Für einen ersten Überblick über die Datenverteilung numerischer Features bietet sich die describe() Methode an. Diese gibt für jede Spalte die Anzahl, Durchschnitt, Standardabweichung, Minimum, Maximum sowie die Quartile an.

# In[85]:


AutoDF.describe().transpose()


# Alle Features haben einen Count von 3337, da dies der Anzahl der Datenpunkt entspricht.
# 
# # Werte ändern sich hier jetzt mit jeder Ausführung. Müssen irgendwann einen Stand safen und den diskutieren

# Nachfolgend wird die Anzahl der unique values je Feature ausgegeben.

# In[86]:


for col in AutoDF.columns:
    values = AutoDF[col].unique()
    print(col, "has", len(AutoDF[col].unique()), "unique values")


# Beschreiben, was wir da sehen

# Als nächstes wird die Anzahl der Fahrzeuge pro Kraftstoffart ausgegeben.

# In[87]:


print(AutoDF['Kraftstoff'].value_counts())


# Die häufigste Kraftstoffart mit xxx Fahrzeugen ist Benzin, gefolgt von Diesel. <br>
# Alle anderen Kraftstoffarten kommen in Relation zur Gesamtmenge an Fahrzeugen eher selten vor.

# Ebenso interessant ist die Anzahl der Fahrzeuge pro Getriebeart.

# In[88]:


print(AutoDF['Getriebe'].value_counts())


# Automatik und Schaltgetriebe kommen ungefähr gleich oft vor. Halbautomatikfahrzeuge kommen dagegen eher selten vor.

# Nachfolgend wird der prozentuale Anteil jeder Automarke in Bezug auf die Gesamtmasse aller Fahrzeuge ausgegeben.

# In[90]:


print(AutoDF['Marke'].value_counts(normalize=True))


# Die häufigste auf Autoscout24 angebotene Automarke ist Mercedes-Benz (16,69%), dicht gefolgt von von BMW (16,63%) und Audi (16,54%). <br>
# Die drei seltensten Automarken sind Smart (0,05%), Land (0,03%) und Jeep (0,03%).

# 

# In[91]:


AutoDF.hist(bins=20, figsize=(20,15))
plt.show()


# In[93]:


fig = px.histogram(AutoDF, x="Preis",title="Distribution over price (Euro)")
pyo.iplot(fig)


# ## Untersuchung der numerischen Variablen

# Um eine erste Übersicht über mögliche Zusammenhänge zwischen den verschiedenen Variablen zu erhalten, wird zunächst ein Pairplot erstellt. Um dn Plot übersichtlich zu halten, werden Variablen ausgewählt, zwischen denen bereits Korrelation vermutet wird.

# In[64]:


sns.pairplot(data=AutoDF, vars=["Preis","PS","km","Verbrauch_l_pro_100km","Emissionen_g_pro_km"], hue="Kraftstoff",)


# In[94]:


sns.lmplot(data=AutoDF, x='PS', y='Preis')


# Tatsächlich können im Pairplot Zusammenhänge zwischen einzelnen Variablen erkannt werden. Vor allem die starke Korrelation zwischen Verbrauch und Emissionen fällt im Plot auf, ist allerdings selbstverständlich da mit höherem Verbrauch in der Regel auch mehr Emissionen erzeugt werden.
# Doch auch weniger starke Abhängigkeiten von bspw. PS auf Preis können erkannt werden.
# 
# Nach der optischen Darstellung sollen nun im nächsten Schritt die Abhängigkeiten noch einmal in Zahlen dargestellt werden.

# In[95]:


corr = AutoDF.corr()
corr['Preis'].sort_values(ascending=False)


# In[96]:


# Create correlation matrix for numerical variables
corr_matrix = AutoDF.corr()
corr_matrix


# In[97]:


# Erstellen einer Heatmap um Abhängigkeiten zwischen den verschiedenen Variablen zu visualisieren

# Use a mask to plot only part of a matrix
mask = np.zeros_like(corr_matrix)
mask[np.triu_indices_from(mask)]= True

# Erstellen der Heatmap mit zusätzlichen Parametern
plt.subplots(figsize=(11, 15))
heatmap = sns.heatmap(corr_matrix, 
                      mask = mask, 
                      square = True, 
                      linewidths = .5,
                      cmap = 'coolwarm',
                      cbar_kws = {'shrink': .6,
                                'ticks' : [-1, -.5, 0, 0.5, 1]},
                      vmin = -1,
                      vmax = 1,
                      annot = True,
                      annot_kws = {"size": 10})


# In[98]:


sns.boxenplot(data=AutoDF, x="Preis", y="Marke", orient="h", width=2)


# was macht sorted_nob ????

# In[99]:


sorted_nb = AutoDF.groupby(['Marke'])['Preis'].median().sort_values()
sorted_nb


# In[100]:


sns.boxplot(x=AutoDF['Marke'], y=AutoDF['Preis'], order=list(sorted_nb.index))


# ### Untersuchung der kategorialen Features

# #### Untersuchung der Features "Ausstattung"

# Als nächstes soll untersucht werden, inwiefern die Ausstattungsmerkmal einen eindeutigen Einfluss auf den Preis haben.

# In[101]:


Austtattung=['Klimaanlage','Alufelgen','Sitzheizung','Einparkhilfe','Navigationssystem']
Austtattung


# In[102]:


fig, ax = plt.subplots(2, 3, figsize=(15, 10))
for var, subplot in zip(Austtattung, ax.flatten()):
    sns.boxplot(x=var, y='Preis', data=AutoDF, ax=subplot)


# Fazit: Keine`??

# #### Untersuchung der Features Kraftstoff, Getriebe

# In[103]:


PriceAveragePerKraftstoff=AutoDF.groupby(by="Kraftstoff")["Preis"].mean()
PriceAveragePerKraftstoff.plot(kind="bar",figsize=(12,6),color="m",title="Average Price per Kraftstoff")


# In[104]:


sns.stripplot(data=AutoDF, x="Kraftstoff", y="Preis" , size=3 )


# In[105]:


Diesel=AutoDF[AutoDF["Kraftstoff"]=="Diesel"]
Benzin=AutoDF[AutoDF["Kraftstoff"]=="Benzin"]
Elektro=AutoDF[AutoDF["Kraftstoff"]=="Elektro"]


# In[85]:


Diesel


# In[106]:


npDiesel = Diesel["Preis"]
npBenzin = Benzin["Preis"]
#npElektro = Elektro["price"]
data = [npDiesel.values, npBenzin.values]
#data = [npDiesel.values, npBenzin.values, npElektro.values]

group_labels = ['Diesel', 'Benzin']
#group_labels = ['Diesel', 'Benzin', 'Elektro']
colors = ['#462EDE', '#DE2EBE', '#FF8033']

# Create distplot with curve_type set to 'normal'
fig = ff.create_distplot(data, group_labels, colors=colors,
                         bin_size=3000, show_rug=False)

# Add title
fig.update_layout(title_text='Hist and Curve Plot')
pyo.iplot(fig)


# In[107]:


fig=px.scatter(AutoDF,x="PS",y="Preis",color="Emissionen_g_pro_km",size="Verbrauch_l_pro_100km",
              hover_data=["Marke","Titel","Kraftstoff"],title="Price over PS",
              trendline="ols")
pyo.iplot(fig)


# ## Kartenvisualisierung

# Als nächstes werden wird der Standort der zum Verkauf angebotenen Fahrzeuge in einer Landkarte visualisiert. <br>
# Für diese Zwecke wurde beim Webcrawling das Attribut Location von Autoscout24 abgezogen und anschließend in der Datenaufbereitung der Stadtname und das Land als extra Spalte angelegt. <br>
# Mithilfe des Geolocators werden jeder Stadt Longitude und Latitude zugeordnet und im Dataframe geoDF gespeichert. Dieses Dataframe wird anschließend über den Index mit dem AutoDF gejoined.

# In[108]:


geolocator = Nominatim(user_agent="my_app")
geoDF = pd.DataFrame()
for city in AutoDF.index:
    try:
        location = geolocator.geocode(AutoDF['Stadt'][city])
        geoDF = geoDF.append({"longitude": location.longitude, "latitude": location.latitude}, ignore_index=True)  
    except:
        geoDF = geoDF.append({"longitude": None, "latitude": None}, ignore_index=True)
geoDF


# In[ ]:


#Index von AutoDF zurücksetzen, da aufgrund der Entfernung der Null-Values bei Verbrauch und Emissionen viele Zeilen weggefallen sind
#sonst kann nicht mit GeoDF gejoined werden
AutoDF = AutoDF.reset_index(drop=True)

#Join von GeoDF und AutoDF über Index
AutoDF = pd.merge(AutoDF, geoDF, left_index=True, right_index=True)


# Unter Verwendung von Longitude und Latitude werden die Fahrzeugstandorte auf einer Folium Map visualisiert. <br>
# Zusätzlich wird jedem Datenpunkt eine Pop-Up Beschreibung hingefügt, welche Stadtname, Autobeschreibung und Preis beinhaltet.

# In[120]:


AutoDF


# In[ ]:


m = folium.Map([50.0 , 10.0],zoom_start=4)
for i in AutoDF.index:
    try:
        folium.Marker( location=[ AutoDF['latitude'][i], AutoDF['longitude'][i] ], popup = [AutoDF['Stadt'][i], AutoDF['Titel'][i], AutoDF['Preis'][i]]).add_to(m)
    except:
        Continue
m

