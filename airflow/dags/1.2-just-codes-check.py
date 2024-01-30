import json
file = open("/home/hdu/airflow/configs/dev.json", 'r')
myconfigs = json.load(file)

print(type(myconfigs))


for key, value in myconfigs.items():
    print(f"\nKey: {key}")
    print(f"Value: {value}\n")

file.close()

