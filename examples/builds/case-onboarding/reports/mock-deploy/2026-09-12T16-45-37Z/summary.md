# Mock deploy result

- org: `sfskills-dev`
- mode: `manifest`
- api version: `67.0` (highest of: M5-S01=67.0, M5-S05=67.0)
- files: 6 file(s) copied, 9 skipped (package.xml/notes)
- status: **Failed**
- checkOnly: `True`
- components: 9 total, 2 ok, 8 error(s)

| Type | Component | Result |
|---|---|---|
|  | BusinessHours | FAIL — The object 'BusinessHours' of type Settings was included in the manifest file package.xml but the associated settings metadata is missing from the 'settings' folder |
|  | Case | FAIL — The object 'Case' of type Settings was included in the manifest file package.xml but the associated settings metadata is missing from the 'settings' folder |
|  | Flow | FAIL — The object 'Flow' of type Settings was included in the manifest file package.xml but the associated settings metadata is missing from the 'settings' folder |
|  | package.xml | ok |
| CustomObject | Case | ok |
| ListView | Case.Billing_Queue | FAIL — In field: queue - no Queue named Billing found |
| ListView | Case.Tier_1_General_Queue | FAIL — In field: queue - no Queue named Tier_1_General found |
| ListView | Case.Tier_2_Queue | FAIL — In field: queue - no Queue named Tier_2_Engineering found |
| Report | Support_Operations/Escalated_Open_Cases | FAIL — Cannot find folder:Support_Operations |
| ReportFolder | Support_Operations | FAIL — In field: sharedTo - no Group named Support_Tier_2 found |

- tests: level RunSpecifiedTests · run 0 · passed 0 · failed 0 · coverage n/a

## Manifest drift

None — the steps' merge matches `reports/MILESTONE-M5-package.xml`.
