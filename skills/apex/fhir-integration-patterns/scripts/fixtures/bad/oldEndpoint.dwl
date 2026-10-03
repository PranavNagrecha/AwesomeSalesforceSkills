%dw 2.0
output application/json
var url = "/services/data/v60.0/healthcare/fhir/R4/Patient/" ++ vars.patientId ++ "/$everything"
---
{ url: url }
