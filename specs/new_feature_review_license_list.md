lets add a new feature that is very simialr to the highlight bad license types.

this feature will take a list of  review license types review_license_type_list

for each of the dependencies that we get, we add a new attribute called review_license. 
we set this to True if any of the licneses associated with a given dependency are in the  review_license_type_list provided by the user. 
when we do this, keep in mind that a single dependency could have mulitple licenses associated and that the license returned by Semgrep API is a list

then we add a new column to the xlsx calls Review_License and this will reflect True or False based on he above

finally for the rows that have review_license = true , we should color code them Yellow

NOTE: this feature is in addition to highlight bad license types feature. useer wants to see both yellow and red highlight at the same time


