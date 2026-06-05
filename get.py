import requests
box = 'https://music.163.com/'
res = requests.get(box)
print(res.text)
