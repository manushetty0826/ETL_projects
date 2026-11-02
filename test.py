from pyspark.sql import SparkSession
from pyspark.sql.functions import avg


spark = SparkSession.builder \
    .appName("SamplePySparkApp") \
    .getOrCreate()

employees = spark.createDataFrame(
    [
        ("Alice", "Engineering", 90000),
        ("Bob", "Sales", 75000),
        ("Carol", "Engineering", 105000),
        ("Dave", "Sales", 80000),
    ],
    ["name", "department", "salary"],
)

average_salaries = employees.groupBy("department").agg(
    avg("salary").alias("average_salary")
)

average_salaries.show()

spark.stop()
