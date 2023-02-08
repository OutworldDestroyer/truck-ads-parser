from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import re 
import json
import os 
import requests

new_data = {}
new_ads = []

xpath = {"title":'//*[@id="content-container-root"]/div[2]/div[1]/div/h1'
	,"price":'//*[@id="content-container-root"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[1]/div[1]/h2',
	"mileage":'//*[@class="itemval"][contains(text(),"km")]',
	"color":'//*[@class="sc-font-bold"][contains(text(),"Farbe")]/following-sibling::div',
	"power":'//*[@class="sc-font-bold"][contains(text(),"Leistung")]/following-sibling::div'}

url = "https://www.truckscout24.de/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage="

current_dir  = os.getcwd()
data_dir = os.path.join(current_dir,"data")
json_dir = os.path.join(data_dir,"data.json")
	
options = Options()
options.add_argument("--headless")
options.add_argument('--ignore-certificate-errors')
	
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def process(ad):
	ad["price"] = re.sub(r'[^0-9]+', r"", ad["price"])
	ad["color"] = str(ad["color"])
	if ad["price"]:
		ad["price"] = int(ad["price"].strip(',-'))
	else:
		ad["price"] = 0
	if ad["mileage"] != 0:
		ad["mileage"] = re.sub(r'[^0-9.]+', r'',ad["mileage"])
		ad["mileage"] = int(float(ad["mileage"].strip()))
	if ad["power"] != 0:
		ad["power"] = int(ad["power"][:ad["power"].find('k')].strip())


def get_by_xpath(name,xpath,ad):
	try:
		elem=driver.find_element(By.XPATH,xpath).get_attribute('innerText')
	except NoSuchElementException:
		if isinstance(ad[name], str):
			return ""
		return 0
	return elem

def download_images(images,ad):
	images_dir = os.path.join(data_dir,str(ad["id"]))
	if not os.path.exists(images_dir):
		os.mkdir(images_dir)
		num = 1
		for image in images:
			image_src = image.get_attribute("data-src")
			response = requests.get(image_src)
			if response.status_code == 200:
				with open(os.path.join(images_dir,"image"+str(num)+".jpg"), 'wb') as f:
					f.write(response.content)
			num += 1



def get_info(num_pages):
	if not os.path.exists(data_dir):
		os.mkdir(data_dir)
	for i in range (1,num_pages+1):
		ad = {"id":i,"href":"","title":"","price":0,"mileage":0,"color":"","power":0,"description":""}
		driver.get(url+str(i))
		item = driver.find_element(By.XPATH,'//*[@class="ls-titles"]/a')
		href = item.get_attribute('href')
		ad["href"] = href
		driver.get(href)
		images = []
		for i in range(1,4):
			images.append(driver.find_element(By.XPATH,f'//*[@id="detpics"]/as24-pictures/div/div[2]/div/as24-carousel[1]/div[1]/div[{i}]/div/img'))
		download_images(images,ad)
		description = ""
		raw_description = driver.find_elements(By.CSS_SELECTOR,'[data-type="description"]')
		if raw_description:
			for paragraph in raw_description: #\xa0\n
				paragraph = paragraph.get_attribute("innerText")
				description += paragraph
		description = description.replace('\xa0\n', ' ')
		description = description.removesuffix('\xa0')
		ad["description"] = description
		for name,path in xpath.items():
			ad[name] = get_by_xpath(name,path,ad)
		process(ad)
		new_ads.append(ad)
		new_data["ads"] = new_ads
	
	if os.path.exists(json_dir):
		with open(json_dir,"r") as file:
			data = json.load(file)
			data.update(new_data)
		with open(json_dir,"w") as file:
			json.dump(data,file)
	else:
		with open(json_dir,"w") as file:
			json.dump(new_data,file)



	print(new_data)
	driver.close()

get_info(4)





