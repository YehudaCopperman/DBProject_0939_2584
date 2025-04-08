# DBProject_0939_2584
## Moshe Goodman 770120939  
## Yehuda Copperman

### about the project



the __project__ of the whole class is to run a gym chain  
this **sub-project** will be managing all the workers within the system which would include all the data and access to the data of the people.  
the data includes personal data, salary, seniority, bunus, contract, and profession/ job.



**person**(**pId**,date of birth, first_name, last_name, email,address, phone)  
* **freelance**(**pId**)  
    * **worker**(**pId**,job_title,contract,hire_date)  
        * **hourly**(**pId**,Hourly_wage,bonus,overtime_rate)  
        * **monthly**(**pId**,vacation_days,monthly_wage,benefits_package)  
* **timespan**(**date**,checkin_time,checkout_time)  
* **services**(**service_name**,equipmant_required)

* **shift**(**pid**,**date**)  
* **serves**(service_nme,pId, service_date_begin,service_date_complete,contract,price)



 
we might wanna add also tax and pension plans to the tables  
maybe it is better to combine the shift and timespan into one table (put into consideration whether you want to have workers clock in twice for the same time)  
we created the ERD and relational schema as shown in the pictures below  



<img src="for_md/erd_diagram.png" width="600" height="400" />    
<img src="for_md/relational_schema.png"  />    


here are three ways where we added data to the tables
1. python copying from shift.csv file using postgres command  
<img src="for_md/python_postgres.png"  />      
3. python using pandas library
<img src="for_md/pandas.png"  />      
5. using the pgadmin interface (pressing the import button.png)    
<img src="for_md/pgadmin_import_button.png"  />      
6. using the query tool in pgadmin  
<img src="for_md/pgadmin_query_tool.png"  />      


below is the picture of the backup and restoration    
  
<img src="for_md/backup_screenshot.png"  />      
<img src="for_md/restoration.jpg"  />      

