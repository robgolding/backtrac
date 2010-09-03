import urllib2, json

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

top_level_url = "http://localhost:8000/api/v1/"

password_mgr.add_password(None, top_level_url, "kaylee", "password")

handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)

print "Enter backup ID:",

backup_id = raw_input()

response = opener.open("http://localhost:8000/api/v1/backups/%d" % int(backup_id))
json_data = response.read()

data = json.loads(json_data)

print data
