'''
DFP Final Project - Fall 2021
Project name: GradCave
Authors:
    -Somya Agarwal - somyaa
    -Shivani Poovaiah Ajjikutira - sajjikut
    -Kristi Kunworee Baishya - kbaishya
    -Kanishka Bhambhani - kbhambha
'''

# Library Imports
import pandas as pd
import xml.etree.cElementTree as et
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import csv
import folium
import webbrowser
from tabulate import tabulate
import warnings
warnings.filterwarnings("ignore")


#setting up chromedriver
def set_up_driver():
    driver= webdriver.Chrome(executable_path="chromedriver.exe")
    return driver

#Scraping Crime Data
def fetch_crimeData():
    #fetch data in xml format from url and store write into a local file
    crimeAPIdata = requests.get('https://data.wprdc.org/datastore/odata3.0/1797ead8-8262-41cc-9099-cbc8a161924b')
    fout=open('apidata.xml','wt',encoding=('utf-8'))
    fout.write(crimeAPIdata.text)
    fout.close()

    #read contents of xml file
    tree=et.parse('apidata.xml')
    root = tree.getroot()
    root.attrib

    #parsing the xml tree to fetch required data and storing in apidata_list
    apidata_list =[]
    for child in root:
        for child2 in child:
            for entry in child2:
                for data in entry:
                    apidata_list.append(data.text)

    #grouping data based on columns
    datacolumns=['_id','PK','CCR','HIERARCHY','INCIDENTTIME','INCIDENTLOCATION','CLEAREDFLAG','INCIDENTNEIGHBORHOOD','INCIDENTZONE','INCIDENTHIERARCHYDESC','OFFENSES','INCIDENTTRACT','COUNCIL_DISTRICT','PUBLIC_WORKS_DIVISION','X','Y']
    datalist=[apidata_list[i:i+16] for i in range(0, len(apidata_list), 16)]
    for index,data in enumerate(datalist):
        check = datalist[index][5].split(",")
        if(len(check)>1):
            datalist[index][5]=check[1].strip('PA ')
            
    #saving the list as a csv file
    with open('crimedata_today.csv', 'w',newline='') as f: 
        write = csv.writer(f)
        write.writerow(datacolumns)
        write.writerows(datalist)


    #create a dataframe from csvFile
    crime_df = pd.read_csv("crimedata_today.csv")
    return crime_df


#counting crime data based on zipcode and location
def crimeCount(crime_df):
    new_df = crime_df.groupby(["INCIDENTLOCATION"])["INCIDENTTIME"].count().reset_index(name="Crime Count")
    final_df = new_df.merge(crime_df,on='INCIDENTLOCATION',how='left')
    #list containing zipcode and crime count in that zipcode
    final_df = final_df[["INCIDENTLOCATION","Crime Count"]]
    return final_df

#Scrapping apartment data
def fetch_apartmentData(driver):
    driver.get("https://www.apartments.com/pittsburgh-pa/")

    driver.implicitly_wait(20)
    apartment_list = []
    property_list = driver.find_elements(By.XPATH,"//div[@class='property-title']")
    price_list = driver.find_elements(By.XPATH,"//*[@class='property-pricing']")
    address_list = driver.find_elements(By.XPATH,"//*[@class='property-address js-url']")

    info = []
    i=0
    for i in range(len(property_list)):
        info = [property_list[i].text, price_list[i].text,address_list[i].text]
        apartment_list.append(info)

    driver.get("https://www.apartments.com/pittsburgh-pa/2")
    driver.implicitly_wait(100000)

    property_list1 = driver.find_elements(By.XPATH,"//div[@class='property-title']")
    price_list1 = driver.find_elements(By.XPATH,"//*[@class='property-pricing']")
    address_list1 = driver.find_elements(By.XPATH,"//*[@class='property-address js-url']")

    info = []
    i=0
    for i in range(len(property_list1)):
        info = [property_list1[i].text, price_list1[i].text,address_list1[i].text]
        apartment_list.append(info)


    driver.get("https://www.apartments.com/pittsburgh-pa/3")
    driver.implicitly_wait(100000)

    property_list2 = driver.find_elements(By.XPATH,"//div[@class='property-title']")
    price_list2 = driver.find_elements(By.XPATH,"//*[@class='property-pricing']")
    address_list2 = driver.find_elements(By.XPATH,"//*[@class='property-address js-url']")

    info = []
    i=0
    for i in range(len(property_list2)):
        info = [property_list2[i].text, price_list2[i].text,address_list2[i].text]
        apartment_list.append(info)
    driver.close()

    for index,data in enumerate(apartment_list):
        check = apartment_list[index][2].split(",")
        apartment_list[index][2]=check[2].strip('PA ')

    with open('apartment_today.csv', 'w',newline='') as f: 
        write = csv.writer(f)
        write.writerows(apartment_list)
#creating a pandas dataframe using scrapped apartment data
def get_apartment_df():
    apartment_df = pd.read_csv("apartment_today.csv",header=None)
    return apartment_df

#Scraping City events data from popularpittsburgh.com 
def fetch_eventsData(driver):
    driver.get("https://popularpittsburgh.com/calendar/#!/")

    driver.implicitly_wait(10000)
    eventList= driver.find_elements(By.XPATH,"//div[@class='cs_sizeBuffer']")
    eventCityList = driver.find_elements(By.XPATH,"//span[@class='cityState hasVenue hideOnListNarrow']")
    eventVenueList = driver.find_elements(By.XPATH,"//span[@cso-text='ev.Venue' and @class='venue']")
    eventTimeList = driver.find_elements(By.XPATH,"//*[@ng-show='ev.HasTime']")

    d1=[]
    d2=[]
    d3=[]
    d4=[]

    for i in range(len(eventList)):
        d1.append(eventList[i].text)
        d2.append(eventVenueList[i].text)
        d3.append(eventCityList[i].text)
        d4.append(eventTimeList[i].text)

    #Reading scraped data to cs
    df = pd.DataFrame({'EventName': d1, 'EventVenue': d2, 'EventCity': d3, 'EventTime': d4})    
    df.to_csv('CityEventsData.csv', index = None)

    city_event_df = pd.read_csv("CityEventsData.csv")
    return city_event_df

#closing chromedriver
def closeDriver(driver):
    driver.close()

#data wrangling and creating map visual using folium library
def mapView_on_html(apartment_df,crime_df):
    apartment_df.rename(columns={0:'ApartmentName',1:'Rate',2:'INCIDENTLOCATION'}, inplace=True)
    apartment_df["INCIDENTLOCATION"] = apartment_df["INCIDENTLOCATION"].astype(str)
    final_df = crime_df.drop_duplicates()
    apartment_crime_df = apartment_df.merge(final_df,on='INCIDENTLOCATION',how='left')
    apartment_crime_df = apartment_crime_df[apartment_crime_df['Crime Count'].notna()]
    zip_codes_df = pd.read_csv("ZipCodes_LatLong.csv")
    final_df_plot = apartment_crime_df.merge(zip_codes_df,on='INCIDENTLOCATION',how='left')
    final_df_plot['Crime Count'] = final_df_plot['Crime Count'].apply(lambda f: format(f, '.0f'))
    final_df_plot['combined']=final_df_plot['ApartmentName'].astype(str)+'('+final_df_plot['Rate']+') '+' , Crimes:'+final_df_plot['Crime Count'].astype(str)
    map = folium.Map(location=[final_df_plot.Latitude.mean(), final_df_plot.Longitude.mean()], zoom_start=14, control_scale=True)

    for index,location_info in final_df_plot.iterrows():
        folium.Marker([location_info["Latitude"], location_info["Longitude"]], popup=location_info["combined"]).add_to(map)
    loc = 'Apartment and Crime Data for Zipcodes in Pittsburgh'
    title_html = '''
                <h3 align="center" style="font-size:24px"><b>{}</b></h3>
                '''.format(loc)   
    map.get_root().html.add_child(folium.Element(title_html))
    map.save("index.html")
    url = "index.html"
    new = 2 # open in a new tab, if possible
    webbrowser.open(url,new=new)

#console input and output based on user input
def user_interaction(apartment_final_df, crime_df, city_event_df):
    print("Welcome to GradCave!!")
    print("\n----------------------------------------------------") 
    flag = True
    while(flag):
        text = input("Enter your desired pincode :")

        if(len(apartment_final_df[apartment_final_df.eq(text).any(1)]) > 0):

            print("\n---Apartment List for the entered zipcode---\n")
            print_apartment_list = apartment_final_df[apartment_final_df.eq(text).any(1)]
            print_apartment_list = print_apartment_list[['ApartmentName','Rate']]
            print(tabulate(print_apartment_list , showindex=False, headers=print_apartment_list.columns))
            print("\n----------------------------------------------------")

            print("\n---Crime List for the entered zipcode---\n")
            print_crime_df= crime_df[crime_df.eq(text).any(1)]
            print_crime_df = print_crime_df.rename(columns={'INCIDENTNEIGHBORHOOD' : 'IncidentNeighborhood','INCIDENTZONE' : 'IncidentZone' ,'OFFENSES' : 'Offenses' ,'INCIDENTTIME' : 'IncidentTime'})
            print_crime_df_final = print_crime_df[['IncidentNeighborhood','IncidentZone','Offenses','IncidentTime']]
            print_crime_df_final['Offenses'] = print_crime_df_final['Offenses'].str[0:100]
            print(tabulate(print_crime_df_final , showindex=False, headers=print_crime_df_final.columns))
            print("\n----------------------------------------------------")

            print("\n------Events of the day nearby------\n")
            print_city_event_df = city_event_df[['EventName','EventCity','EventVenue','EventTime']]
            print(tabulate(print_city_event_df , showindex=False, headers=city_event_df.columns))
            print("\n----------------------------------------------------")     
        else:
            print("\n----------------------------------------------------\n")
            print("No data for the given pincode. Please try with a new one")
        print("\n----------------------------------------------------\n")
        user = input("Do you want to search for another zipcode (Y/N) :")
        if(user == 'N' or user == 'n'):
            flag = False
            print("\n----------------------------------------------------\n")
            print("Have a great day!")
    
#Function calls
driver = set_up_driver()
fetched_crime_df = fetch_crimeData()
crime_df = crimeCount(fetched_crime_df)
fetch_apartmentData(driver)
apartment_df = get_apartment_df()
driver = set_up_driver()
city_event_df = fetch_eventsData(driver)
closeDriver(driver)
mapView_on_html(apartment_df,crime_df)
user_interaction(apartment_df, fetched_crime_df, city_event_df)

    
    








