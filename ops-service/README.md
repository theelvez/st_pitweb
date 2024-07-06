# ops-service
ops-service is the website and database for operations at the Sun Valley Tour de Force.  These operations include: Run Management and Results Tracking
## how to run
`python ops-service.py`
## how to view the site
http://localhost
## how to setup the database
The database needs to exist at `instance\SVTdF-2024.sqlite`.  A sample database, found in the `sample-database` directory, can be used to seed this   
## TODO list
### scheduling
- add car flow
- add laser top speed flow
- auto-schedule shouldn't put same person in back-to-back heats
### upload
- test advanced upload
### advanced statistics
- run external app to process?
- write in Python?
- populate advanced table
- separate page for extended results

