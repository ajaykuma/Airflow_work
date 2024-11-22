from pyspark.sql import SparkSession
from pyspark.conf import SparkConf

#Defining spark
"""spark = SparkSession.builder.appName("sparkdfex2").getOrCreate()"""

#Or
"""spark = SparkSession.builder.appName("sparkdfex1").master("local[*]").getOrCreate()"""

# Create a SparkConf object to specify configs
"""conf = SparkConf().setAppName("MyApp").setMaster("local[*]") \
            .set("spark.executor.memory", "2g") \
            .set("spark,sql.shuffle.partitions", 2)
spark = SparkSession.builder.config(conf=conf).getOrCreate()

# Retrieve the SparkConf object from the SparkContext
conf = spark.sparkContext.getConf()

# Print the configuration settings
print("spark.app.name = ", conf.get("spark.app.name"))
print("spark.master = ", conf.get("spark.master"))
print("spark.executor.memory = ", conf.get("spark.executor.memory"))"""

#since using airflow to run spark appls, we can specify configs within dag's task
spark = SparkSession.builder.getOrCreate()

def spafunc():
    data = spark.read.format('csv') \
    .option('header','true') \
    .option('inferSchema','true') \
    .load("file:///home/hdu/Downloads/Bank_full.csv")
    #data.write.mode('overwrite').save('/home/hdu/my-venv/sampleoutpt')
    return data.show(2)

spafunc()
