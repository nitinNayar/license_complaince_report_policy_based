lets add a new feature 

this feature will take a list of bad license types bad_license_type_list

for each of the dependencies that we get, we add a new attribute called bad_license. 
we set this to True if any of the licneses associated with a given dependency are in the  bad_license_type_list provided by the user. 
when we do this, keep in mind that a single dependency could have mulitple licenses associated and that the license returned by Semgrep API is a list

then we add a new column to the xlsx calls Bad_License and this will reflect True or False based on he above

finally for the rows that have bad_license = true , we should color code them red

