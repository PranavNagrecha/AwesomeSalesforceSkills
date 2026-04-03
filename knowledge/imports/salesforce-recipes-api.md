

Data Prep Recipe REST API
## Developer Guide
## Salesforce, Spring ’26
Last updated: March 20, 2026

## ©
Copyright 2000–2026 Salesforce, Inc. All rights reserved. Salesforce is a registered trademark of Salesforce, Inc., as are other
names and marks. Other marks appearing herein may be trademarks of their respective owners.

## CONTENTS
DATA PREP RECIPE REST API OVERVIEW. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Release  Notes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
Connect REST API Authorization. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
API  End-of-Life  Policy. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
EXAMPLES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
Manage, Schedule, and Run Recipes with REST APIs. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3
RESOURCES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
Recipe  Resources. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 8
REQUESTS. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 18
Abstract  Bucket  Algorithm  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 25
Aggregate  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
Aggregate  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 26
Aggregate  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
Append Mapping Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
Append  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 27
Append Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Append V2 Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Bucket  Date  Argument  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 28
Bucket Date Bucket Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
Bucket Date Only Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 29
Bucket  Date  Setup  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
Bucket Date Source Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 30
Bucket Date Time Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Bucket Dimension Bucket Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Bucket  Dimension  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Bucket Dimension Setup Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 31
Bucket Dimension Source Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 32
Bucket Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 32
Bucket Measure Bucket Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
Bucket  Measure  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
Bucket  Measure  Setup  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 33
Bucket Measure Source Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
Bucket  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
Bucket Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 35
Bucket  Setup  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 35
Bucket  Term  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 35

Bucket  V2  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
Bucket V2 Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 36
Bucket V2 Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
Cluster  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 37
Cluster  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 38
Compute Relative Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 38
Compute  Relative  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
Compute  Relative  Sort  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39
Data  Object  Category  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
Detect  Sentiment  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
Detect Sentiment Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 40
Discovery  Contributor  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Discovery  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Discovery  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41
Export  Limits  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
Export  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42
Export  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
Extension  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 43
Extension Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44
Extract Grain Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 44
Extract Grain Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
Extract  Grain  Parameter  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
Extract Grain Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
Filter Expression Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
Filter  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
Filter  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Flatten Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Flatten  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Flatten Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Format  Date  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Format Date Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Format  Date  Pattern  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Formula  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Formula Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 50
Join  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 50
Join Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 50
Load Analytics Dataset Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
Load  Connected  Dataset  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 51
Load  Data  Lake  Object  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 52
Load Data Model Object Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 52
Load Dataset Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 52
Load  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53
Load  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 53
Legacy  Formula  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 54
## Contents

Legacy Formula Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 54
Measure  To  Currency  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55
Optimized Append Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55
Optimized  Append  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55
Optimized Update Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 56
Optimized Update Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 56
Output D360 Fields Mapping Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 57
Output D360 Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 57
Output D360 Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58
Output Data Cloud Fields Mapping Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 58
Output Data Cloud Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 59
Output Data Cloud Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 59
Output External Fields Mapping Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61
Output  External  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61
Output  External  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61
Pivot Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
Pivot  V2  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 62
Predict  Values  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Predict Values Input Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Predict Values Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 63
Predict Values Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64
Predict Values Setup Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64
Recipe  Configuration  Collection  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 64
Recipe  Configuration  Fiscal  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65
Recipe Configuration Fiscal Offset Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 65
Recipe  Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 66
Recipe Conversion Detail Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 66
Recipe  Definition  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 67
Recipe  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 68
Recipe  Name  Label  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 69
Recipe  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 70
Recipe Notification Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 71
Recipe Type Name Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
Recommendation  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
Recommendation  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 72
Sample  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 73
Streaming  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 74
Save  Dataset  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 74
Save  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 75
Save  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 75
Schema  Field  Format  Symbols  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Schema  Field  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Schema  Field  Properties  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 76
Schema Field Type Properties Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 77
## Contents

Schema  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 77
Schema Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Schema Slice Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Split  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
Split Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
SQL Filter Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
SQL  Filter  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79
SQL Formula Date Only Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
SQL  Formula  Date  Time  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
SQL Formula Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 80
SQL  Formula  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81
SQL Formula Multivalue Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81
SQL  Formula  Numeric  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 82
SQL Formula Text Field Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 82
Target  Field  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 82
Time Series Input Confidence Interval High Low. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 83
Time Series Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 83
Time Series Parameters Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 84
Time Series V2 Algorithm Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 85
Time Series V2 Forecast Info Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 85
Time Series V2 Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Time  Series  V2  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 86
Typecast Node Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
Typecast  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 87
Typographic  Cluster  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Update  Data  Cloud  Object  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Update  Data  Cloud  Object  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 88
Update  Node  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
Update  Parameters  Input. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 90
RESPONSES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 92
Abstract  Bucket  Algorithm. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 99
Aggregate. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 99
Aggregate  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
Aggregate  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 100
Append  Mapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
Append Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
Append  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 101
AppendV2  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 102
Bucket Date Argument. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 102
Bucket  Date  Bucket. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
Bucket Dimension Bucket. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
Bucket  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 103
Bucket  Measure  Bucket. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
## Contents

Bucket  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Bucket  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 104
Bucket  Setup. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 105
Bucket Source Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 105
Bucket  V2  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 106
Bucket Term. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 106
Bucket  V2  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 107
Bucket  V2  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 107
Bucket. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 108
Cluster  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 108
Cluster  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 108
Compute Relative Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 109
Compute Relative Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 109
Compute Relative Sort Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110
Data Object Category. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110
Detect  Sentiment  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Detect Sentiment Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Discovery  Contributor. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 111
Discovery Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 112
Discovery  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 112
Discovery Source. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Export  Limits. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Export  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Export Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 113
Extension Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
Extension  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 114
Extract  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Extract Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115
Extract  Parameter. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Extract  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Filter  Expression. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 116
Filter  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117
Filter  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117
Flatten  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Flatten Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Flatten  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118
Format Date Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Format  Date  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Format Date Pattern. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 119
Formula  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Formula  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Join  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120
Join  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121
Load Analytics Dataset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 121
## Contents

Load  Connected  Dataset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 122
Load Data Lake Object. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 122
Load  Data  Model  Object. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 123
Load  Dataset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 123
Load  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 123
Load  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 124
Legacy Formula Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 124
Legacy Formula Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
Measure  To  Currency. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
Optimized Append Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 125
Optimized Append Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 126
Optimized  Update  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 126
Optimized  Update  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 126
Output  D360  Fields  Mapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 127
Output  D360  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 127
Output D360 Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Output  Data  Cloud  Fields  Mapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 128
Output  Data  Cloud  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 129
Output Data Cloud Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 129
Output External Field Mapping. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 131
Output External Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 131
Output  External  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 132
Pivot. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 132
PivotV2. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Predict Values Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Predict Values Input Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 133
Predict  Values  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 134
Predict Values Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 134
Predict  Values  Setup. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 134
Recipe  Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 134
Recipe Configuration Collection. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 135
Recipe Configuration Fiscal. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 135
Recipe  Configuration  Fiscal  Offset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Recipe Configuration. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Recipe  Conversion  Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 136
Recipe Definition. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 137
Recipe Name Label. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 138
Recipe  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 139
Recipe  Notification. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 140
Recipe  Validation  Detail. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 141
Recipe. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 141
Recommendation Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 143
Recommendation  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 144
Sample  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 144
## Contents

Save  Dataset. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 145
Save Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 146
Save  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 146
Schema Field Format Symbols. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 146
Schema  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 147
Schema  Field  New  Properties. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 147
Schema  Field  Type  Properties. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 147
Schema  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 148
Schema  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 148
Schema  Slice. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 149
Split  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 149
Split  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 149
SQL Filter Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 150
SQL Filter Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 150
SQL  Formula  Date  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 150
SQL  Formula  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 151
SQL  Formula  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 151
SQL  Formula  Multivalue  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
SQL Formula Numeric Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
SQL Formula Text Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
Streaming Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 152
Target  Field. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 153
Time  Series  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 153
Time Series Output Confidence Interval High Low. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 154
Time Series Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 154
Time  Series  V2  Algorithm  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 155
Time Series V2 Forecast Info. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 156
Time Series V2 Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 156
Time Series V2 Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 156
Typecast  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 158
Typecast Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 158
Typographic  Cluster. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 158
Update Data Cloud Object Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 159
Update  Data  Cloud  Object  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 159
Update  Node. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 161
Update  Parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 161
APPENDICES. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 162
Recipe  REST  API  Enums. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 162
## Contents



## DATA PREP RECIPE REST API OVERVIEW
You can access Data Prep recipes for CDP, Salesforce Data Pipelines, and CRM Analytics programmatically using the Recipe REST API.
Using the Recipe REST API, you can:
## •
Run, schedule, and sync recipes. See Run, Schedule, and Sync CRM Analytics Data with REST APIs
## •
Retrieve or update recipe metadata. See Build, Manage, Schedule, and Run Recipes with REST APIs
The Recipe REST API is based on the Connect REST API and follows its conventions. For more information about the Connect REST API,
see the Connect REST API Developer Guide.
For more information on Analytics asset resources, like connectors and datasets, see the Analytics REST API Developer Guide.
Data Prep Recipes Connect REST API Release Notes
Use the Salesforce Release Notes to learn about the most recent updates and changes to the Data Prep Recipes Connect REST API.
Connect REST API Authorization
Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.
API End-of-Life Policy
Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.
Data Prep Recipes Connect REST API Release Notes
Use the Salesforce Release Notes to learn about the most recent updates and changes to the Data Prep Recipes Connect REST API.
For new and changed Data Prep Recipes REST resources and request and response bodies see CRM Analytics in the Salesforce Release
Notes and look for Data Prep Recipes REST API.
Note:  If the API: New and Changed Items section in the Salesforce Release Notes isn’t present, there aren’t any updates for that
release.
Connect REST API Authorization
Connect REST API uses OAuth to securely identify your application before connecting to Salesforce.
OAuth and Connect REST API
For current OAuth information, see OAuth and Connect REST API in the Connect REST API developer guide.
## More Resources
Salesforce offers the following resources to help you navigate connected apps and OAuth:
## •
## Salesforce Help: Connected Apps
## •
Salesforce Help: Authorize Apps with OAuth
## 1

## •
Salesforce Help: OpenID Connect Token Introspection
## •
## Trailhead: Build Integrations Using Connected Apps
API End-of-Life Policy
Salesforce is committed to supporting each API version for a minimum of three years from the date of first release. In order to mature
and improve the quality and performance of the API, versions that are more than three years old might cease to be supported.
When an API version is to be deprecated, advance notice is given at least one year before support ends. Salesforce will directly notify
customers using API versions planned for deprecation.
Version Retirement InfoVersion Support StatusSalesforce API Versions
Supported.Versions 31.0 through 66.0
Salesforce Platform API Versions 21.0 through 30.0
## Retirement
As of Summer ’25, these versions are retired
and unavailable.
Versions 21.0 through 30.0
Salesforce Platform API Versions 7.0 through 20.0
## Retirement
As of Summer ’22, these versions are retired
and unavailable.
Versions 7.0 through 20.0
If you request any resource or use an operation from a retired API version, REST API returns 410:GONE error code.
To identify requests made from old or unsupported API versions of REST API, access the free API Total Usage event type.
## 2
API End-of-Life PolicyData Prep Recipe REST API Overview

## RECIPE REST API EXAMPLES
Use Recipe REST API examples to perform tasks.
While using the Recipe REST API, remember:
## •
Request parameters can be included as part of the Recipe REST API resource URL, for example, /wave/recipes?q=searchtext.
A request body is a rich input that can be included as part of the request. When accessing a resource, you can use either a request
body or request parameters. You can’t use both.
## •
With a request body, use Content-Type:application/json or Content-Type:application/xml.
## •
With request parameters, use Content-Type:application/x-www-form-urlencoded.
Manage, Schedule, and Run Recipes with REST APIs
Use the Salesforce Connect REST API to work with and automate recipes. Discover your existing recipes, revert recipe versions, and
schedule and run recipes.
Manage, Schedule, and Run Recipes with REST APIs
Use the Salesforce Connect REST API to work with and automate recipes. Discover your existing recipes, revert recipe versions, and
schedule and run recipes.
Describe and Discover Recipes
Retrieve all your recipes with the GET wave/recipes endpoint. You can filter the recipes collection returned by:
## •
format— specifies current Data Prep recipes: (R3) or Data Prep Classic recipes (R2).
/wave/recipes?format=R2
## •
licenseType— specifies the license type: EinsteinAnalytics, Sonic, MulesoftDataPath, or Cdp.
/wave/recipes?licenseType=EinsteinAnalytics
## •
pageSize— the number of items to be returned in the collection for pagination. The minimum is 1, maximum is 200, and default
is 25.
/wave/recipes?pageSize=50
## •
q— Use search terms to find recipes by name or label. Individual terms are separated by spaces. A wildcard is automatically appended
to the last token in the query string.
/wave/recipes?q=MyRecipe
## •
sort— The type of sort order to be applied to the returned collection. Valid values are App, CreatedBy, CreatedDate,
LastModified, LastModifiedBy, Mru, Name, and Type.
/wave/recipes?sort=Name
## 3

Tip:  The Lightning Web Component wire adapter, lightning/analyticsWaveApigetRecipes() provides the
same functionality inside Lightning Experience.
Describe an existing recipe by specifying the recipeId (starts with 05vB) and the format of the recipe: R3 or R2.
/wave/recipes/05vB0000000xxxxxxx?format=R3
Important:  Recipes created in v48 or higher can only be R3 and can’t be converted to R2.
The GET request returns a Recipe response, which contains the recipe definition (nodes and UI metadata), schedule attributes, and
validation details. It also contains the targetDataflowId, used to run the recipe. For example, GET
/wave/recipes/05vB0000000xxxxxxx?format=R3 returns this Recipe JSON response:
## {
## ...
"format": "R3",
"id": "05vB0000000xxxxxxx",
"label": "MyTestRecipe",
"name": "MyTestRecipe",
## ...
"recipeDefinition": {
## ...
## },
"scheduleAttributes": {
## ...
## },
"targetDataflowId": "02KB000000xxxxxxxx",
## ...
"validationDetails": [ ]
## }
Use the Recipe JSON response to work with the recipe as detailed.
Tip:  The Lightning Web Component wire adapter, lightning/analyticsWaveApigetRecipe() provides the same
functionality inside Lightning Experience.
## Inspect Recipe Nodes
The RecipeDefinition contains the recipe name, the recipe API version, the UI metadata for recipe display (used by Data
Manager), and a Map of RecipeNode objects.
Here’s a closer look at the Map of RecipeNode objects in the RecipeDefinition object from the Recipe JSON response.
The example response is a simple recipe that loads data created from the Opportunities sObject, filters the data by Closed Won, and
saves the results to a new dataset named Opptys Closed Won.
## {
## ...
"recipeDefinition":{
## "nodes": {
## "LOAD_DATASET0":  {
## "action": "load",
## "parameters":{
## "dataset": {
"label": "Opportunities",
## "name": "opportunity",
## 4
Manage, Schedule, and Run Recipes with REST APIsRecipe REST API Examples

"type": "analyticsDataset"
## },
"fields": ["AccountId","Amount","OpenClosedWonLost",...]
## },
## "sources": []
## },
## "FILTER0": {
## "action": "filter",
## "parameters": {
"filterExpressions": [ {
"field": "OpenClosedWonLost",
"operands": [ "ClosedWon"],
"operator": "EQUAL",
"type": "TEXT"
## } ]
## },
"sources":[ "LOAD_DATASET0"]
## },
## "OUTPUT0": {
## "action": "save",
## "parameters":{
## "dataset": {
"folderName": "SharedApp",
"label": "OpptysClosedWon",
"name": "OpptysClosedWon",
"type": "analyticsDataset"
## },
## "fields": []
## },
"sources": [ "FILTER0"]
## }
## },
## "ui": { ... },
## "version": "52.0"
## },
## ...
## }
Each node entry in the map has a string name and RecipeNode. The RecipeNode contains the node action, parameters, and
sources. Each node type has different parameters based on the action. For more information on each node type, see the Recipe Node
reference.
Important:  The label attribute of the dataset attribute for the save action is the display name of the dataset users can
explore in Analytics Studio.
Delete a Recipe
To delete a recipe, use the DELETE /wave/recipes/<recipeId> endpoint. This action deletes the recipe and any associated
dataflow jobs. No request body is required and the response is a success or error message.
Tip:  The Lightning Web Component wire adapter, lightning/analyticsWaveApideleteRecipe() provides the
same functionality inside Lightning Experience.
## 5
Manage, Schedule, and Run Recipes with REST APIsRecipe REST API Examples

Work with Recipe Histories
Each time a user updates and saves a recipe, a version history is created, tracking the changes to the recipe over time. To see all of the
histories for a recipe, use the GET /wave/recipes/<recipeId>/histories endpoint.
To revert a current recipe to a previous version, get the id of the history you want to revert to and use the PUT
/wave/recipes/<recipeId> endpoint with the AssetReviewHistoryInput request.
## {
"historyId": "0RmB0000000xxxxxxx",
"historyLabel": "Revertingto versionx"
## }
For more information on asset version histories, see Backup and Restore Previous Versions of CRM Analytics Assets with History API.
Schedule a Recipe
While the scheduleAttributes are part of the Recipe, to update a schedule, the /wave/asset/<assetId>/schedule
endpoint must be used.
To see the current schedule, use GET /wave/asset/<assetId>/schedule, where <assetId> is the recipe id. The request
returns a Schedule response.
To create or update the schedule, use PUT /wave/asset/<assetId>/schedule. See Schedule Dataflows, Recipes, and Data
Syncs for example ScheduleInput requests.
To delete a schedule, use DELETE /wave/asset/<assetId>/schedule.
Run a Recipe
To run a recipe, with or without a schedule, use the /wave/dataflowjobs POST endpoint.
The POST takes a dataflowId and a command to start the dataflow job. For a recipe, the dataflowId is the
targetDataflowId from the Recipe. For recipes, the targetDataflowId starts with 02KB.
After retrieving the targetDataflowId from the GET /wave/recipes/05vB0000000xxxxxxx?format=R3 response,
use it in the POST /wave/dataflowjobs JSON request body.
## {
"dataflowId":"02KB000000xxxxxxxx",
## "command":"start"
## }
To stop a running recipe dataflow job, use the /wave/dataflowjobs/<dataflowjobId> PATCH endpoint with the command
to stop.
## {
## "command":"stop"
## }
## Recipe Notifications
Recipe notifications alert users when jobs are long running or fail. All recipes are created with a default notification level of warnings.
To see the notification level for a recipe, use the GET /wave/recipes/<recipeId>/notification endpoint. To update
## 6
Manage, Schedule, and Run Recipes with REST APIsRecipe REST API Examples

the notification level or the long running alert timing, use the PUT /wave/recipes/<recipeId>/notification endpoint
with a RecipeNotificationInput on page 71 request.
## {
"notificationLevel": "Always",
"longRunningAlertInMins": 90
## }
## 7
Manage, Schedule, and Run Recipes with REST APIsRecipe REST API Examples

## RECIPES REST RESOURCES
REST API resources are sometimes called endpoints.
## Recipe Resources
Recipes are used to prepare data, creating a dataset or updating an sObject using transformations to manipulate the data.
## Recipe Resources
Recipes are used to prepare data, creating a dataset or updating an sObject using transformations to manipulate the data.
## Available Resources
Resource URLSupported
## HTTP
## Method
DescriptionResource
/wave/recipesGET POSTReturns a collection of Data Prep recipes and
creates a recipe.
## Recipes List
## Resource
/wave/recipes/<id>GET
## DELETE
## PATCH
Returns, updates, or deletes a Data Prep recipe.Recipe Resource
/wave/recipes/<id>/fileGETReturns a Data Prep recipe's file content as JSON.Recipe File
## Resource
/wave/recipes/<id>/notificationGET
## PATCH
Returns a Data Prep recipe job notification,
creates, or updates a Data Prep recipe job
notification.
## Recipe
## Notification
## Resource
/wave/recipes-configurationsGET
## PATCH
## POST
Returns or updates a collection of Data Prep
recipe configurations and creates a recipe
configuration.
## Recipe
## Configurations
## List Resource
/wave/recipe-configurations/<id>GET
## DELETE
## PATCH
Returns, updates, or deletes a Data Prep recipe
configuration.
## Recipe
## Configuration
## Resource
## Recipes List Resource
Returns a collection of Data Prep recipes and creates a recipe.
## Recipe Resource
Returns, updates, or deletes a Data Prep recipe.
## 8

## Recipe File Resource
Returns a Data Prep recipe's file content as JSON. This API endpoint is internal for the recipe UI and is available for debugging and
reference purposes only. Modification of this content is not supported.
## Recipe Notification Resource
Returns a Data Prep recipe job notification, creates, or updates a Data Prep recipe job notification.
## Recipe Configurations List Resource
Returns and updates a collection of Data Prep recipe configurations and creates a recipe configuration.
## Recipe Configuration Resource
Returns a Data Prep recipe configuration and updates or deletes the configuration.
## Recipes List Resource
Returns a collection of Data Prep recipes and creates a recipe.
Resource URL
## /wave/recipes
## Formats
## JSON
## Available Version
## 38.0
Available in Postman
To view and test a working example of this resource, see getRecipeCollection in Postman. For information about how to authenticate
your org with Postman, see the CRM Analytics Rest API Quickstart.
## Available Components
## •
LWC — lightning/analyticsWaveApigetRecipes()
HTTP Methods
## GET
Request Parameters for GET
Available VersionRequired or
## Optional
DescriptionTypeParameter Name
61.0OptionalReturns a collection filtered by recipes
belonging to the specified folder ID.
IdfolderId
## 9
Recipes List ResourceRecipes REST Resources

Available VersionRequired or
## Optional
DescriptionTypeParameter Name
48.0OptionalReturns a collection filtered by the format
of the current recipe definition. Valid values
are:
ConnectRecipe
FormatTypeEnum
format
## •
R2 (Data Prep Classic)
## •
R3 (Data Prep)
55.0OptionalReturns a collection filtered by recipes with
a last modified date after the given value.
StringlastModified
## After
55.0OptionalReturns a collection filtered by recipes with
a last modified date before the given value.
StringlastModified
## Before
52.0OptionalFilters the collection by the Analytics license
type. Valid values are
ConnectAnalytics
LicenseTypeEnum
licenseType
## •
Cdp (Data 360)
## •
DataPipelineQuery (Data
## Pipeline Query)
## •
EinsteinAnalytics (CRM
## Analytics)
## •
IntelligentApps (Intelligent
## Apps)
## •
MulesoftDataPath (Mulesoft
## Data Works)
## •
Sonic (Salesforce Data Pipeline)
55.0OptionalReturns a collection filtered by recipes with
a scheduled run after the given value.
StringnextScheduled
## After
55.0OptionalReturns a collection filtered by recipes with
a scheduled run before the given value.
StringnextScheduled
## Before
38.0OptionalA generated token that indicates the view
of the objects to be returned.
## Stringpage
38.0OptionalNumber of items to be returned in a single
page. Minimum is 1, maximum is 200, and
the default is 25.
IntpageSize
38.0OptionalSearch terms. Individual terms are separated
by spaces. A wildcard is automatically
## Stringq
appended to the last token in the query
string. If the user’s search query contains
quotation marks or wildcards, those symbols
are automatically removed from the query
string in the URI along with any other special
characters.
## 10
Recipes List ResourceRecipes REST Resources

Available VersionRequired or
## Optional
DescriptionTypeParameter Name
38.0OptionalThe type of sort order to be applied to the
returned collection. Valid values are:
ConnectWaveSort
OrderTypeEnum
sort
## •
## App
## •
CreatedBy
## •
CreatedById
## •
CreatedDate
## •
FolderName
## •
LastModified
## •
LastModifiedBy
## •
LastModifiedById
## •
LastModifiedDate
## •
## Location
## •
Mru (Most Recently Used, last viewed
date)
## •
## Name
## •
## Outcome
## •
RefreshDate (for assets like
datasets)
## •
RunDate (for assets like reports)
## •
## Status
## •
## Title
## •
## Type
55.0OptionalReturns a collection filtered by the statuses
of the recipe. Valid values are:
ConnectRecipeStatus
## Enum[]
status
## •
## Cancelled
## •
## Failure
## •
New (Never run or has no recent run)
## •
## Queued
## •
## Running
## •
## Success
## •
## Warning
The following REST URL shows how to use the q parameter as a search query in the GET request.
/wave/recipes?q=MyRecipe
## 11
Recipes List ResourceRecipes REST Resources

Response Body for GET
## Recipe Collection
Important:  Recipes require the recipe editor UI for creation and aren’t supported using POST via this API endpoint.
## Recipe Resource
Returns, updates, or deletes a Data Prep recipe.
Resource URL
## /wave/recipes/<id>
## Formats
## JSON
## Available Version
## 38.0
Available in Postman
To view and test a working example of this resource, see getRecipe in Postman. For information about how to authenticate your org
with Postman, see the CRM Analytics Rest API Quickstart.
## Available Components
## •
LWC — lightning/analyticsWaveApideleteRecipe()
## •
LWC — lightning/analyticsWaveApigetRecipe()
## •
LWC — lightning/analyticsWaveApiupdateRecipe()
HTTP Methods
## DELETE GET PATCH PUT
Run a Recipe
To run a Data Prep recipe, use the Dataflow Jobs Resource API. For examples of how to start and stop recipes, see Start and Stop a
Dataflow Job or Recipe.
Schedule a Recipe
To schedule a recipe, use the Schedule Resource API. For examples of how to schedule recipes, see Schedule Dataflows, Recipes, and
## Data Syncs.
## 12
Recipe ResourceRecipes REST Resources

Request Parameters for GET
Available VersionRequired or
## Optional
DescriptionTypeParameter Name
49.0Required for Data
Prep recipes,
Specifies the format of the returned recipe.
Valid values are:
ConnectRecipe
FormatTypeEnum
format
Optional for Data
Prep Classic recipes.
## •
R2 (Data Prep Classic)
## •
R3 (Data Prep)
51.0OptionalUse the history ID to request a specific recipe
version.
IdhistoryId
The following REST URL shows how to use the format request parameter to return a Data Prep recipe via the GET request.
/wave/recipes/<05vS7000000xxxxxxx>?format=R3
Note:  With API version 49.0 and higher, the format request parameter is required for recipes created in the Data Prep format.
For recipes created in the Data Prep Classic format, the format request parameter isn’t needed. If you want to up-convert the
Data Prep Classic recipe format to the Data Prep recipe format, use the format request parameter set to R3.
Response Body for GET, PATCH, and PUT
## Recipe
Request Body for PATCH
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredIndicates whether editor validation for the
recipe is enabled (true) or not ( false).
BooleanenableEditor
## Validation
38.0RequiredThe recipe file.BinaryrecipeFile
38.0RequiredThe recipe definition.RecipeInput[]recipeObject
53.0RequiredThe recipe validation context. Valid values
are:
ConnectRecipe
ValidationContext
## Enum
validation
## Context
## •
## Default
## •
## Editor
The following JSON shows how to update a recipe, specifically the license type for the recipe.
## {
"recipeObject": {
"licenseAttributes":{ "type":"Sonic"}
## 13
Recipe ResourceRecipes REST Resources

## }
## }
Note:  If the recipe was created in the Data Prep Classic format, then is retrieved in the Data Prep format, a PATCH request with
the Data Prep format up-converts the recipe permanently to the Data Prep format.
Request Body for PUT
Use the PUT API request to revert to a previous historical version. Asset Revert History Input The following JSON shows the revert request
for a recipe version.
## {
"historyId": "0RmRM000000xxxxxxx"
## }
## Recipe File Resource
Returns a Data Prep recipe's file content as JSON. This API endpoint is internal for the recipe UI and is available for debugging and
reference purposes only. Modification of this content is not supported.
Resource URL
## /wave/recipes/<id>/file
## Formats
## JSON
## Available Version
## 38.0
HTTP Methods
## GET
Response Body for GET
StreamedRepresentation. Returns a binary stream of the JSON contents of the specified file. This representation is different
for recipe 2.0 and recipe 3.0.
## Recipe Notification Resource
Returns a Data Prep recipe job notification, creates, or updates a Data Prep recipe job notification.
## 14
Recipe File ResourceRecipes REST Resources

Resource URL
## /wave/recipes/<id>/notification
## Formats
## JSON
## Available Version
## 49.0
Available in Postman
To view and test a working example of this resource, see getRecipeNotification in Postman. For information about how to authenticate
your org with Postman, CRM Analytics Rest API Quickstart.
## Available Components
## •
LWC — lightning/analyticsWaveApigetRecipeNotification()
HTTP Methods
## GET PUT
Response Body for GET and PUT
## Recipe Notification
Request Body for PUT
Recipe Notification Input The following JSON shows how to update an existing recipe notification.
## {
"longRunningAlertInMins": 60,
"notificationLevel":"Warnings"
## }
## Recipe Configurations List Resource
Returns and updates a collection of Data Prep recipe configurations and creates a recipe configuration.
Resource URL
## /wave/recipe-configurations
## 15
Recipe Configurations List ResourceRecipes REST Resources

## Formats
## JSON
## Available Version
## 54.0
HTTP Methods
## GET POST PATCH
Response Body for GET and PATCH
## Recipe Configuration Collection
Request Body for POST
## Recipe Configuration Input
Response Body for POST
## Recipe Configuration
Request Body for PATCH
## Recipe Configuration Collection Input
## Recipe Configuration Resource
Returns a Data Prep recipe configuration and updates or deletes the configuration.
Resource URL
## /wave/recipe-configurations/<id>
## Formats
## JSON
## Available Version
## 54.0
HTTP Methods
## GET DELETE PATCH
## 16
Recipe Configuration ResourceRecipes REST Resources

Response Body for GET and PATCH
## Recipe Configuration
Request Body for PATCH
## Recipe Configuration Input
## 17
Recipe Configuration ResourceRecipes REST Resources

## RECIPE REST API REQUEST BODIES
To perform a POST, PATCH, or PUT request, pass query parameters or create a request body formatted in either XML or JSON. This chapter
lists the request bodies. The query parameters are listed with each resource.
To create a JSON request body, specify the properties of the request body in JSON format.
This is an example of a Comment request body.
## {
"body": "Let'slookfor a new solution."
## }
If a request body is top-level, it has a root XML tag listed. To create an XML request body, nest the properties as XML tags inside the root
XML tag.
This is the same request body in XML format:
## <comment>
<body>Let'slookfor a new solution.</body>
## </comment>
## Abstract Bucket Algorithm Input
The base bucket algorithm for a recipe.
## Aggregate Input
The aggregate data for a recipe node.
## Aggregate Node Input
An aggregate data node in a recipe.
## Aggregate Parameters Input
The parameters for an aggregate data node in a recipe.
## Append Mapping Input
A mapping for an append node in a recipe.
## Append Node Input
An append node in a recipe.
## Append Parameters Input
The parameters for an append node in a recipe.
## Append V2 Node Input
A version 2 append node in a recipe.
## Bucket Date Argument Input
The argument for a bucket node date field in a recipe.
## Bucket Date Bucket Input
A bucket for a bucket node date field in a recipe.
## Bucket Date Only Field Input
A date only field for a bucket node in a recipe.
## 18

## Bucket Date Setup Input
The date setup for a bucket node in a recipe.
## Bucket Date Source Field Input
A date source field for a bucket node in a recipe.
## Bucket Date Time Field Input
A date time field for a bucket node in a recipe.
## Bucket Dimension Bucket Input
A bucket for a bucket node dimension field in a recipe.
## Bucket Dimension Field Input
A dimension field for a bucket node in a recipe.
## Bucket Dimension Setup Input
The dimension field setup for a bucket node in a recipe.
## Bucket Dimension Source Field Input
A dimension source field for a bucket node in a recipe.
## Bucket Field Input
A field for a bucket node in a recipe.
## Bucket Measure Bucket Input
A bucket for a bucket node measure field in a recipe.
## Bucket Measure Field Input
A measure field for a bucket node in a recipe.
## Bucket Measure Setup Input
The measure field setup for a bucket node in a recipe.
## Bucket Measure Source Field Input
A measure source field for a bucket node in a recipe.
## Bucket Node Input
A bucket node in a recipe.
## Bucket Parameters
The parameters for a bucket node in a recipe.
## Bucket Setup Input
The base field setup for a bucket node in a recipe.
## Bucket Term Input
A bucket term in a recipe node.
## Bucket V2 Input
A version 2 bucket in a recipe.
## Bucket V2 Node Input
A version 2 bucket node in a recipe, with improved functionality.
## Bucket V2 Parameters Input
A paramters for a version 2 bucket node in a recipe.
## Cluster Node Input
A cluster node in a recipe.
## 19
Recipe REST API Request Bodies

## Cluster Parameters
The parameters for a cluster node in a recipe.
## Compute Relative Node Input
A compute relative node in a recipe.
## Compute Relative Parameters Input
The parameters for a compute relative node in a recipe.
## Compute Relative Sort Parameters Input
The sort parameters for a compute relative node in a recipe.
## Data Object Category Input
The data object category for an Output Data Cloud node.
## Detect Sentiment Node Input
A detect sentiment node in a recipe.
## Detect Sentiment Parameters Input
The parameters for a detect sentiment node in a recipe.
## Discovery Contributor Input
The discovery contributor for an Einstein Discovery prediction field.
## Discovery Node Input
An Einstein Discovery prediction node in a recipe.
## Discovery Parameters Input
The parameters for an Einstein Discovery prediction node in a recipe.
## Export Limits Input
The limits for an export node in a recipe.
## Export Node Input
An export node in a recipe.
## Export Parameters Input
The parameters for an export node in a recipe.
## Extension Node Input
An extension node in a recipe.
## Extension Parameters Input
The parameters for an extension node in a recipe.
## Extract Grain Field Input
An extract grain field.
## Extract Grain Node Input
An extract grain node in a recipe.
## Extract Grain Parameter Input
A parameter for an extract grain field.
## Extract Grain Parameters Input
The parameters for an extract grain node in a recipe.
## Filter Expression Input
A regex expression for a filter.
## 20
Recipe REST API Request Bodies

## Filter Node Input
A filter node in a recipe.
## Filter Parameters Input
The parameters for a filter node in a recipe.
## Flatten Field Input
A field for a flatten node in a recipe.
## Flatten Node Input
A flatten node in a recipe.
## Flatten Parameters Input
The parameters for a flatten node in a recipe.
## Format Date Node Input
A date format conversion node in a recipe.
## Format Date Parameters Input
The parameters for a date format conversion node in a recipe.
## Format Date Pattern Input
The pattern for date format conversion.
## Formula Node Input
A formula node in a recipe.
## Formula Parameters Input
The base parameters for a formula node in a recipe.
## Join Node Input
A join node in a recipe.
## Join Parameters Input
The parameters for a join node in a recipe.
## Load Analytics Dataset Input
A CRM Analytics dataset to load.
## Load Connected Dataset Input
A connected dataset to load.
## Load Data Lake Object Input
A data lake object to load.
## Load Data Model Object Input
A data model object to load.
## Load Dataset Input
The base dataset for a load node in a recipe.
## Load Node Input
A load node in a recipe.
## Load Parameters Input
The parameters for a load node in a recipe.
## Legacy Formula Field Input
A legacy formula field for a formula.
## 21
Recipe REST API Request Bodies

## Legacy Formula Parameters Input
The legacy formula parameters for a formula.
## Measure To Currency Input
The conversion information for currency measure field.
## Optimized Append Node Input
An optimized append node in a recipe.
## Optimized Append Parameters Input
The parameters for an optimized append node in a recipe.
## Optimized Update Node Input
An optimized append node in a recipe.
## Optimized Update Parameters Input
The parameters for an optimized update node in a recipe.
## Output D360 Fields Mapping Input
The fields mapping for an output D360 node in a recipe.
## Output D360 Node Input
An output D360 node in a recipe.
## Output D360 Parameters Input
The parameters for an output D360 node in a recipe.
## Output Data Cloud Fields Mapping Input
The fields mapping for an output Data 360 node in a recipe.
## Output Data Cloud Node Input
An output Data 360 node in a recipe.
## Output Data Cloud Parameters Input
The parameters for an output Data 360 node in a recipe.
## Output External Fields Mapping Input
A field mapping for an output external node in a recipe.
## Output External Node Input
An output external node in a recipe.
## Output External Parameters Input
The parameters for an output external node in a recipe.
## Pivot Input
A pivot for an aggregate data node in a recipe.
## Pivot V2 Input
A version 2 pivot for an aggregate data node in a recipe.
## Predict Values Field Input
A field for a predict values node in a recipe.
## Predict Values Input Field Input
An input field for a predict values node in a recipe.
## Predict Values Node Input
A predict missing values node in a recipe.
## 22
Recipe REST API Request Bodies

## Predict Values Parameters Input
The parameters for a predict values node in a recipe.
## Predict Values Setup Input
The setup for a predict values node field.
## Recipe Configuration Collection Input
A collection of data prep recipe configurations.
## Recipe Configuration Fiscal Input
The data prep recipe fiscal configuration data.
## Recipe Configuration Fiscal Offset Input
The data prep recipe fiscal offset configuration data.
## Recipe Configuration
A data prep recipe configuration.
## Recipe Conversion Detail Input
The details for the upconversion of a data prep recipe.
## Recipe Definition Input
The definition for a data prep recipe. Available on for R3 recipes.
## Recipe Input
A data prep recipe.
## Recipe Name Label Input
The name and label for a field in a recipe node.
## Recipe Node Input
The base node for a recipe.
## Recipe Notification Input
A notification for a data prep recipe.
## Recipe Type Name Input
The name and type for a field in a recipe node.
## Recommendation Node Input
A recommendation node in a recipe.
## Recommendation Parameters Input
The parameters for a recommendation node in a recipe.
## Sample Parameters Input
The sample parameters for loading data.
## Streaming Parameters Input
The streaming parameters for loading data.
## Save Dataset Input
The dataset for a save node in a recipe.
## Save Node Input
A save data node in a recipe.
## Save Parameters Input
The parameters for a save node in a recipe.
## 23
Recipe REST API Request Bodies

## Schema Field Format Symbols Input
The field format symbols for a schema node in a recipe.
## Schema Field Parameters Input
The field parameters for a schema node in a recipe.
## Schema Field Properties Input
The field properties for a schema node in a recipe.
## Schema Field Type Properties Input
The field type properties for a schema node in a recipe.
## Schema Node Input
A schema node in a recipe.
## Schema Parameters Input
The parameters for a schema node in a recipe.
## Schema Slice Input
The slice definition for a schema node in a recipe.
## Split Node Input
A split node in a recipe.
## Split Parameters Input
The parameters for a split node in a recipe.
SQL Filter Node Input
A SQL filter node in a recipe.
SQL Filter Parameters Input
The parameters for a SQL filter node in a recipe.
SQL Formula Date Only Field Input
The SQL formula date only field for a recipe node.
SQL Formula Date Time Field Input
The SQL formula date time field for a recipe node.
SQL Formula Field Input
The base SQL formula field for a recipe node.
SQL Formula Parameters Input
The SQL formula parameters for a formula.
SQL Formula Multivalue Field Input
The SQL formula multivalue field for a recipe node.
SQL Formula Numeric Field Input
The SQL formula numeric field for a recipe node.
SQL Formula Text Field Input
The SQL formula text field for a recipe node.
## Target Field Input
A target field for a recipe bucket.
## Time Series Input Confidence Interval High Low
A confidence interval for a time series recipe node.
## 24
Recipe REST API Request Bodies

## Time Series Node Input
A time series node in a recipe.
## Time Series Parameters Input
The parameters for a time series node in a recipe.
## Time Series V2 Algorithm Input
The algorithm for a time series version 2 node in a recipe.
## Time Series V2 Forecast Info Input
The forecast info for a time series version 2 node in a recipe.
## Time Series V2 Node Input
A time series version 2 node in a recipe.
## Time Series V2 Parameters Input
The parameters for a time series version 2 node in a recipe.
## Typecast Node Input
A typecast node in a recipe.
## Typecast Parameters Input
The parameters for a typecast node in a recipe.
## Typographic Cluster Input
The configuration for a typographic cluster algorithm.
## Update Data Cloud Object Node Input
A Data 360 object update node in a recipe.
## Update Data Cloud Object Parameters Input
The parameters for an update data cloud object node in a recipe.
## Update Node Input
An update node in a recipe.
## Update Parameters Input
The parameters for an update node in a recipe.
## Abstract Bucket Algorithm Input
The base bucket algorithm for a recipe.
## Properties
Inherited by Typographic Cluster Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe algorithm type of the recipe bucket
field. Valid values are:
RecipeBucket
AlgorithmType
type
## •
TypographicClustering
## 25
Abstract Bucket Algorithm InputRecipe REST API Request Bodies

## Aggregate Input
The aggregate data for a recipe node.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe recipe aggregation type. Valid values
are:
RecipeAggregate
## Type
action
## •
## Avg
## •
## Count
## •
## Maximum
## •
## Median
## •
## Minimum
## •
StdDev
## •
StdDevP
## •
## Sum
## •
## Unique
## •
## Var
## •
VarP
49.0RequiredThe label for the aggregate data.Stringlabel
49.0RequiredThe name for the aggregate data.Stringname
49.0RequiredThe source for the aggregate data.Stringsource
## Aggregate Node Input
An aggregate data node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe parameters for the node.Aggregate
ParametersInput
parameters
## 26
Aggregate InputRecipe REST API Request Bodies

## Aggregate Parameters Input
The parameters for an aggregate data node in a recipe.
## Properties
## Available
## Version
Required or
## Optional
DescriptionTypeProperty
## Name
49.0RequiredThe list of aggregations for the node.AggregateInput[]aggregations
49.0RequiredThe list of groupings for the node.String[]groupings
49.0RequiredThe aggregate type for the node.
Valid values are:
RecipeAggregate
NodeEnum
nodeType
## •
## Hierarchical
## •
## Standard
53.0RequiredThe parent field for the nodeStringparentField
53.0RequiredThe percentage field for the nodeStringpercentage
## Field
54.0OptionalThe pivot v2 data for the node.PivotV2Input[]pivot_v2
51.0RequiredThe list of pivots for the node.PivotInput[]pivots
53.0RequiredThe self field for the nodeStringselfField
## Append Mapping Input
A mapping for an append node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe bottom dataset field.Stringbottom
51.0RequiredThe top dataset field.Stringtop
## Append Node Input
An append node in a recipe.
## 27
Aggregate Parameters InputRecipe REST API Request Bodies

## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe parameters for the node.AppendParameters
## Input
parameters
## Append Parameters Input
The parameters for an append node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
55.0OptionalIndicates whether disjoint schema merge is
allowed when automatically mapping fields
(true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
51.0RequiredThe list of mappings for the node.AppendMapping
## Input[]
fieldMappings
## Append V2 Node Input
A version 2 append node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe parameters for the node.AppendParameters
## Input
parameters
## Bucket Date Argument Input
The argument for a bucket node date field in a recipe.
## 28
Append Parameters InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe date argument.Longargument
51.0RequiredThe bucket grain for the field. Valid values
are:
RecipeBucketGraintype
## •
AbsoluteDate
## •
## Days
## •
FiscalQuarters
## •
FiscalYears
## •
## Months
## •
## Quarters
## •
## Weeks
## •
## Years
## Bucket Date Bucket Input
A bucket for a bucket node date field in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe date range end.BucketDate
ArgumentInput
rangeEnd
51.0RequiredThe date range start.BucketDate
ArgumentInput
rangeStart
51.0RequiredThe date value.Stringvalue
## Bucket Date Only Field Input
A date only field for a bucket node in a recipe.
## Properties
Inherits properties from Bucket Field Input.
## 29
Bucket Date Bucket InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe setup for the date bucket.BucketDateSetup
## Input
bucketsSetup
## Bucket Date Setup Input
The date setup for a bucket node in a recipe.
## Properties
Inherits properties from Bucket Setup Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of buckets.BucketDateBucket
## Input[]
buckets
51.0RequiredThe source field.BucketDateSource
FieldInput
sourceField
## Bucket Date Source Field Input
A date source field for a bucket node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe name of the field.Stringname
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## 30
Bucket Date Setup InputRecipe REST API Request Bodies

## Bucket Date Time Field Input
A date time field for a bucket node in a recipe.
## Properties
Inherits properties from Bucket Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe setup for the date bucket.BucketDateSetup
## Input
bucketsSetup
## Bucket Dimension Bucket Input
A bucket for a bucket node dimension field in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of source values.String[]sourceValues
51.0RequiredThe dimension value.Stringvalue
## Bucket Dimension Field Input
A dimension field for a bucket node in a recipe.
## Properties
Inherits properties from Bucket Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe setup for a dimension field.BucketDimension
SetupInput
bucketsSetup
## Bucket Dimension Setup Input
The dimension field setup for a bucket node in a recipe.
## 31
Bucket Date Time Field InputRecipe REST API Request Bodies

## Properties
Inherits properties from Bucket Setup Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of buckets.BucketDimension
BucketInput[]
buckets
51.0RequiredThe source field.BucketDimension
SourceFieldInput
sourceField
## Bucket Dimension Source Field Input
A dimension source field for a bucket node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe name of the field.Stringname
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Bucket Field Input
A field for a bucket node in a recipe.
## Properties
Inherited by Bucket Date Only Field Input, Bucket Date Time Field Input, Bucket Dimension Field Input, and Bucket Measure Field Input
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe bucket field property label.Stringlabel
51.0RequiredThe bucket field property name.Stringname
## 32
Bucket Dimension Source Field InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Bucket Measure Bucket Input
A bucket for a bucket node measure field in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe range end.DoublerangeEnd
51.0RequiredThe range start.DoublerangeStart
51.0RequiredThe measure value.Stringvalue
## Bucket Measure Field Input
A measure field for a bucket node in a recipe.
## Properties
Inherits properties from Bucket Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe setup for a measure field.BucketMeasureSetup
## Input
bucketsSetup
## Bucket Measure Setup Input
The measure field setup for a bucket node in a recipe.
## 33
Bucket Measure Bucket InputRecipe REST API Request Bodies

## Properties
Inherits properties from Bucket Setup Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of buckets.BucketMeasure
BucketInput[]
buckets
51.0RequiredThe source field.BucketMeasure
SourceFieldInput
sourceField
## Bucket Measure Source Field Input
A measure source field for a bucket node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe name of the field.Stringname
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Bucket Node Input
A bucket node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the bucket node.BucketParameters
## Input
parameters
## 34
Bucket Measure Source Field InputRecipe REST API Request Bodies

## Bucket Parameters
The parameters for a bucket node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of fields for the node. Valid bucket
fields are:
BucketFieldInput[]fields
## •
BucketDateOnlyFieldInput
## •
BucketDateTimeFieldInput
## •
BucketDimensionFieldInput
## •
BucketMeasureFieldInput
## Bucket Setup Input
The base field setup for a bucket node in a recipe.
## Properties
d
Inherited by Bucket Date Setup Input, Bucket Dimension Setup Input, and Bucket Measure Setup Input
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe bucketing algorithm. Valid values are:AbstractBucket
AlgorithmInput
algorithm
## •
TypographicClusterInput
51.0RequiredThe default bucket value.StringdefaultBucket
## Value
51.0RequiredIndicates whether pass through is enabled
(true) or not (false).
BooleanisPassThrough
## Enabled
51.0RequiredThe null bucket valueStringnullBucket
## Value
## Bucket Term Input
A bucket term in a recipe node.
## 35
Bucket ParametersRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredThe recipe node data type. Valid recipe data
types are:
RecipeDataTypeopType
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
64.0RequiredA map of operands for the bucket term.Map<Object,
## Object>
operands
64.0RequiredThe operator for the bucket term.Stringoperator
## Bucket V2 Input
A version 2 bucket in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0OptionalA boolean expression for the bucket.StringbooleanLogic
64.0OptionalThe list of terms for the bucket.BucketTermInput on
page 35[]
terms
64.0RequiredThe value for the bucket.Stringvalue
## Bucket V2 Node Input
A version 2 bucket node in a recipe, with improved functionality.
## Properties
Inherits properties from Recipe Node Input on page 70.
## 36
Bucket V2 InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredThe parameters for the V2 bucket node.BucketV2Parameters
Input on page 37
parameters
## Bucket V2 Parameters Input
A paramters for a version 2 bucket node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredThe bucket algorithm. Valid bucket
algorithms are:
AbstractBucket
AlgorithmInput on
page 25[]
algorithm
## •
TypographicClusterInput on page 88
64.0RequiredA list of the buckets for the node.BucketV2Input on
page 36[]
buckets
64.0RequiredA default bucket for the node.ObjectdefaultBucket
64.0OptionalIndicates whether the bucket result is
multi-value (true) or not (false).
booleanmultiValue
## Result
64.0OptionalA null bucket for the node.ObjectnullBucket
64.0OptionalIndicates whether pass through is enabled
for the bucket (true) or not (false).
booleanpassthrough
## Enabled
64.0RequiredThe source field for the bucket.StringsourceField
64.0RequiredThe target field for the bucket.TargetFieldInput on
page 82
targetField
## Cluster Node Input
A cluster node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 37
Bucket V2 Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the bucket node.ClusterParameters
## Input
parameters
## Cluster Parameters
The parameters for a cluster node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe cluster count.IntegerclusterCount
53.0RequiredIndicates whether to find the optimal
clusters (true) or (not).
BooleanfindOptimal
## Clusters
53.0RequiredIndicates whether to produce scaled
columns (true) or (not).
BooleanproduceScaled
## Columns
53.0RequiredThe scaling type. Valid values are:MeasureScalingType
## Enum
scaling
## •
MinMaxScaling
51.0RequiredThe source fields.String[]sourceFields
51.0RequiredThe target field.RecipeNameLabel
## Input
targetField
53.0RequiredA list of target scaled fields.RecipeNameLabel
## Input[]
targetScaled
## Fields
## Compute Relative Node Input
A compute relative node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.ComputeRelative
ParametersInput
parameters
## 38
Cluster ParametersRecipe REST API Request Bodies

## Compute Relative Parameters Input
The parameters for a compute relative node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe formula expression type. Valid values
are:
RecipeFormula
ExpressionType
expression
## Type
## •
## Legacy
## •
## Sql
51.0RequiredThe list of formula fields. Valid values are:SqlFormulaField
## Input[]
fields
## •
SQL Formula Date Only Field Input
## •
SQL Formula Date Time Field Input
## •
SQL Formula Multivalue Field Input
## •
SQL Formula Numeric Field Input
## •
SQL Formula Text Field Input
51.0OptionalThe list of sort fields.ComputeRelativeSort
ParametersInput[]
orderBy
51.0OptionalThe list of partition by values.String[]partitionBy
## Compute Relative Sort Parameters Input
The sort parameters for a compute relative node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe sort direction. Valid values are:RecipeSortOrder
## Enum
direction
## •
## Ascending
## •
## Descending
51.0RequiredThe field name.StringfieldName
## 39
Compute Relative Parameters InputRecipe REST API Request Bodies

## Data Object Category Input
The data object category for an Output Data Cloud node.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0RequiredThe name of the data category.StringcategoryName
60.0RequiredThe label of the data category.Stringlabel
## Detect Sentiment Node Input
A detect sentiment node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.DetectSentiment
ParametersInput
parameters
## Detect Sentiment Parameters Input
The parameters for a detect sentiment node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe output type. Valid values are:DetectSentiment
OutputTypeEnum
outputType
## •
## Dimension
## •
## Measure
54.0RequiredThe sentiment score type. Valid values are:SentimentScoreType
## Enum
sentiment
## Score
## •
## All
## •
## None
## 40
Data Object Category InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe source field.StringsourceField
51.0RequiredThe target field.RecipeNameLabel
## Input
targetField
54.0RequiredThe collection of target confidence fields.Map<String,
Map<String, Recipe
NameLabelInput>
target
## Sentiment
ScoreFields
## Discovery Contributor Input
The discovery contributor for an Einstein Discovery prediction field.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe discovery field.RecipeNameLabel
## Input
field
51.0RequiredThe discovery impact.RecipeNameLabel
## Input
impact
## Discovery Node Input
An Einstein Discovery prediction node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.DiscoveryParameters
## Input
parameters
## Discovery Parameters Input
The parameters for an Einstein Discovery prediction node in a recipe.
## 41
Discovery Contributor InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe map of column mappings.Map<String, String>columnMapping
56.0RequiredThe list of multiclass fields.DiscoveryContributor
## Input[]
multiClass
## Fields
51.0RequiredThe prediction source.RecipeTypeName
## Input
predictSource
51.0RequiredThe list of prediction factor fields.DiscoveryContributor
## Input[]
prediction
FactorFields
51.0RequiredThe prediction field.RecipeNameLabel
## Input
prediction
## Field
51.0RequiredThe list of prescription fields.DiscoveryContributor
## Input[]
prescription
## Fields
## Export Limits Input
The limits for an export node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe maximum file size for the export
partition.
IntegermaxFileSizeIn
## Bytes
51.0RequiredThe maximum row count for the export
partition.
IntegermaxRowCount
## Export Node Input
An export node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 42
Export Limits InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.ExportParameters
## Input
parameters
## Export Parameters Input
The parameters for an export node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredThe type of the recipe export CSV header
row value. Valid values are:
RecipeExportCsv
HeaderRowValue
## Type
csvHeaderRow
ValueType
## •
FullyQualifiedName
## •
## Label
51.0RequiredThe list of fields to export.String[]fields
51.0RequiredThe format of the export.Stringformat
51.0RequiredThe limits to export.ExportLimitsInputlimitsPerPart
51.0RequiredThe user ID with access to the exported
data.
StringuserId
## Extension Node Input
An extension node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.ExtensionParameters
## Input
parameters
## 43
Export Parameters InputRecipe REST API Request Bodies

## Extension Parameters Input
The parameters for an extension node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredA map of extension arguments, defined by
the extension definition
Map<Object,
## Object>
args
56.0RequiredThe name of the extension.Stringname
56.0RequiredThe namespace of the extension.Stringnamespace
56.0RequiredThe version of the extension.Doubleversion
## Extract Grain Field Input
An extract grain field.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe extract grain type. Valid values are:RecipeDateGraingrainType
## •
## Day
## •
DayEpoch
## •
FiscalMonth
## •
FiscalQuarter
## •
FiscalWeek
## •
FiscalYear
## •
## Hour
## •
## Minute
## •
## Month
## •
## Quarter
## •
## Second
## •
SecondEpoch
## •
## Week
## •
## Year
51.0RequiredThe extract field label.Stringlabel
## 44
Extension Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe extract field name.Stringname
## Extract Grain Node Input
An extract grain node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.ExtractGrain
ParametersInput
parameters
## Extract Grain Parameter Input
A parameter for an extract grain field.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe source field.Stringsource
51.0RequiredThe list of grain fields.ExtractGrainField
## Input[]
targets
## Extract Grain Parameters Input
The parameters for an extract grain node in a recipe.
## 45
Extract Grain Node InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe date configuration name.Stringdate
## Configuration
## Name
51.0RequiredThe date fields to extract grains for.ExtractGrain
ParameterInput[]
grain
## Extractions
## Filter Expression Input
A regex expression for a filter.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe field to filter on.Stringfield
51.0RequiredThe list of operands.Object[]operands
51.0RequiredThe operator to use for the filter.Stringoperator
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Filter Node Input
A filter node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 46
Filter Expression InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.FilterParameters
## Input
parameters
## Filter Parameters Input
The parameters for a filter node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0OptionalThe filter boolean logic.StringfilterBoolean
## Logic
51.0RequiredThe list of filter expressions.FilterExpression
## Input[]
filter
## Expressions
## Flatten Field Input
A field for a flatten node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredIndicates whether the field is a system field
(true) or not (false).
BooleanisSystemField
51.0RequiredThe field label.Stringlabel
51.0RequiredThe field name.Stringname
## Flatten Node Input
A flatten node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 47
Filter Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.FlattenParameters
## Input
parameters
## Flatten Parameters Input
The parameters for a flatten node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredIndicates whether to include the self-ID
(true) or not (false).
BooleanincludeSelfId
51.0RequiredThe multi field.FlattenFieldInputmultiField
51.0RequiredThe parent field.StringparentField
51.0RequiredThe path field.FlattenFieldInputpathField
51.0RequiredThe self-field.StringselfField
## Format Date Node Input
A date format conversion node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.FormatDate
ParametersInput
parameters
## Format Date Parameters Input
The parameters for a date format conversion node in a recipe.
## 48
Flatten Parameters InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe source field.StringsourceField
51.0RequiredThe list of source date formats.FormatDatePattern
## Input[]
sourceFormats
51.0RequiredThe target field.RecipeNameLabel
## Input
targetField
51.0RequiredThe target date format.FormatDatePattern
## Input
targetFormat
## Format Date Pattern Input
The pattern for date format conversion.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of values for construction of the date
format.
## String[]construction
51.0RequiredThe list of date format groups.String[]groups
51.0OptionalThe regular expression for the date format.Stringregex
## Formula Node Input
A formula node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node. Valid values
are:
FormulaParameters
## Input
parameters
## •
LegacyFormulaParametersInput
## •
SqlFormulaParametersInput
## 49
Format Date Pattern InputRecipe REST API Request Bodies

## Formula Parameters Input
The base parameters for a formula node in a recipe.
## Properties
Inherited by LegacyFormulaParametersInput and SqlFormulaParametersInput.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe formula expression type. Valid values
are:
RecipeFormula
ExpressionType
expression
## Type
## •
## Legacy
## •
## Sql
## Join Node Input
A join node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.JoinParametersInputparameters
## Join Parameters Input
The parameters for a join node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe join type. Valid values are:RecipeJoinTypejoinType
## •
## Cross
## •
## Inner
## •
LeftOuter
## •
## Lookup
## 50
Formula Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
MultiValueLookup
## •
## Outer
## •
RightOuter
51.0RequiredThe list of left keys.String[]leftKeys
51.0RequiredThe left qualifier.StringleftQualifier
51.0RequiredThe list of right keys.String[]rightKeys
51.0RequiredThe right qualifier.Stringright
## Qualifier
## Load Analytics Dataset Input
A CRM Analytics dataset to load.
## Properties
Inherits properties from Load Dataset Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe dataset name.Stringname
## Load Connected Dataset Input
A connected dataset to load.
## Properties
Inherits properties from Load Dataset Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe name of the connection.Stringconnection
## Name
52.0OptionalThe pushdown filter.FilterParameters
## Input
filter
## 51
Load Analytics Dataset InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
65.0Optional>The mode for accessing connected
datasets. Valid values are:
ConnectedMode
## Enum
mode
## •
## AUTO
## •
## DIRECT
## •
## SYNCED
51.0RequiredThe name of the source object.StringsourceObject
## Name
## Load Data Lake Object Input
A data lake object to load.
## Properties
Inherits properties from Load Dataset Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe data lake object name.Stringname
## Load Data Model Object Input
A data model object to load.
## Properties
Inherits properties from Load Dataset Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe data model object name.Stringname
## Load Dataset Input
The base dataset for a load node in a recipe.
## 52
Load Data Lake Object InputRecipe REST API Request Bodies

## Properties
Inherited by Load Analytics Dataset Input, Load Connected Dataset Input, Load Data Lake Object Input, and Load Data Model ObjectInput.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe type of the dataset. Valid values are:RecipeDatasetTypetype
## •
## Analytics
## •
## Connected
## •
DataLakeObject
## •
DataModelObject
## Load Node Input
A load node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.LoadParameters
## Input
parameters
## Load Parameters Input
The parameters for a load node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe dataset to load. Valid values are:LoadDatasetInputdataset
## •
## Load Analytics Dataset Input
## •
## Load Connected Dataset Input
## •
## Load Data Lake Object Input
## •
Load Data Model ObjectInput
51.0RequiredThe list of fields to load.String[]fields
## 53
Load Node InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
65.0OptionalThe list of fields to preserve currency for.String[]preserve
## Currency
## Fields
57.0OptionalIndicates whether to purge the cache
(true) or not (false).
BooleanpurgeCache
57.0OptionalThe input run mode. Valid values are:InputRunModeEnumrunMode
## •
## Full
## •
## Incremental
## •
## Streaming
55.0RequiredThe sample parameters for the dataset load.SampleParameters
## Input
sampleDetails
51.0RequiredThe number of rows to load.IntegersampleSize
## Legacy Formula Field Input
A legacy formula field for a formula.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe formula expression.Stringformula
## Expression
51.0RequiredThe field label.Stringlabel
51.0RequiredThe field name.Stringname
## Legacy Formula Parameters Input
The legacy formula parameters for a formula.
## Properties
Inherits properties from Formula Parameters Input.
## 54
Legacy Formula Field InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of fields.LegacyFormulaField
## Input[]
fields
## Measure To Currency Input
The conversion information for currency measure field.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe conversion rate date field.Stringconversion
RateDateField
56.0RequiredThe measure field.StringmeasureField
## Optimized Append Node Input
An optimized append node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
62.0RequiredThe parameters for the node.OptimizedAppend
ParametersInput
parameters
## Optimized Append Parameters Input
The parameters for an optimized append node in a recipe.
## 55
Measure To Currency InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
62.0RequiredIndicates whether disjoint schema merge is
allowed (true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
62.0RequiredThe base dataset to append.LoadAnalytics
DatatsetInput
dataset
62.0RequiredThe name of the date configuration.Stringdate
## Configuration
## Name
64.0RequiredThe append operation type. Valid operation
types are:
OperationEnumoperation
## •
## Append
## •
## Delete
## •
## Upsert
## Optimized Update Node Input
An optimized append node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
62.0RequiredThe parameters for the node.OptimizedUpdate
ParametersInput
parameters
## Optimized Update Parameters Input
The parameters for an optimized update node in a recipe.
## 56
Optimized Update Node InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredIndicates whether disjoint schema merge is
allowed (true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
64.0RequiredThe base dataset to append.LoadAnalytics
DatatsetInput
dataset
64.0RequiredThe name of the date configuration.Stringdate
## Configuration
## Name
64.0RequiredThe append operation type. Valid operation
types are:
OperationEnumoperation
## •
## Append
## •
## Delete
## •
## Upsert
## Output D360 Fields Mapping Input
The fields mapping for an output D360 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe name of the source field.StringsourceField
56.0RequiredThe name of the target field.StringtargetField
## Output D360 Node Input
An output D360 node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 57
Output D360 Fields Mapping InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe parameters for the node.OutputD360
ParametersInput
parameters
## Output D360 Parameters Input
The parameters for an output D360 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe list of field mappings.OutputD360Fields
MappingInput[]
fieldsMapping
56.0RequiredThe name of the D360 object.Stringname
57.0RequiredThe streaming parameters.Streaming
ParametersInput[]
streaming
56.0RequiredThe output type. Valid values are:RecipeD360Output
## Type
type
## •
DateLakeObject
## Output Data Cloud Fields Mapping Input
The fields mapping for an output Data 360 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
60.0RequiredThe data type of the target field.StringdataType
60.0RequiredThe name of the source field.StringsourceField
60.0RequiredThe name of the target field.StringtargetField
60.0RequiredThe label of the target field.StringtargetLabel
## 58
Output D360 Parameters InputRecipe REST API Request Bodies

## Output Data Cloud Node Input
An output Data 360 node in a recipe.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
60.0RequiredThe parameters for the node.OutputDataCloud
ParametersInput
parameters
## Output Data Cloud Parameters Input
The parameters for an output Data 360 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
60.0RequiredThe data category for the data lake object
## (DLO).
DataObjectCategory
## Input
category
60.0RequiredThe output connector type. Valid values are:ConnectWaveData
ConnectorTypeEnum
connectorType
## •
AmazonAthena
## •
AmazonRedshiftOutput
## •
AmazonS3
## •
AmazonS3Output
## •
AmazonS3Private
## •
AwsRdsAuroraMySQL
## •
AwsRdsAuroraPostgres
## •
AwsRdsMariaDB
## •
AwsRdsMySQL
## •
AwsRdsPostgres
## •
AwsRdsSqlServer
## •
AzureDataLakeGen2Output
## •
AzureSqlDatabase
## •
AzureSqlDatawarehouse
## 59
Output Data Cloud Node InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
Databricks(Beta)
## •
GoogleAnalytics4
## •
GoogleBigQuery
## •
GoogleBigQueryDirect
## •
GoogleBigQueryStandardSQL
## •
GoogleSpanner
## •
HerokuPostgres
## •
HubSpot
## •
MarketoV2
## •
NetSuite
## •
OracleEloqua
## •
## Redshift
## •
RedshiftPrivate
## •
SalesforceExternal
## •
SalesforceMarketingCloud
OAuth2
## •
SapHanaCloud
## •
SfdcLocal
## •
SnowflakeComputing
## •
SnowflakeDirect
## •
SnowflakeOutput
## •
SnowflakePrivate
## •
SnowflakePrivateOutput
## •
TableauOnline
## •
TableauHyperOutput
## •
## Zendesk
DEPRECATED: min
60.0, max 64.0
RequiredThe dataspace to use in Data 360.AssetReferenceInputdataspace
60.0RequiredA list of dataspaces to use in Data 360.AssetReference
## Input[]
dataspaces
66.0OptionalThe event time field.StringeventTime
## Field
60.0RequiredThe list of field mappings.OutputDataCloud
FieldsMapping
## Input[]
fieldsMapping
60.0RequiredThe label of the Data 360 object.Stringlabel
60.0RequiredThe name of the Data 360 object.Stringname
## 60
Output Data Cloud Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
60.0RequiredThe name of the primary key field for the
Data 360 object.
StringprimaryKey
60.0RequiredThe output type. Valid values are:RecipeDataCloud
OutputTypeEnum
type
## •
DateLakeObject
## Output External Fields Mapping Input
A field mapping for an output external node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe name of the source field.StringsourceField
51.0RequiredThe name of the target field.StringtargetField
## Output External Node Input
An output external node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
56.0RequiredThe parameters for the node.OutputExternal
ParametersInput
parameters
## Output External Parameters Input
The parameters for an output external node in a recipe.
## 61
Output External Fields Mapping InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe connection name.Stringconnection
## Name
51.0RequiredThe field name for the external ID.StringexternalId
FieldName
56.0RequiredThe list of field mappings.OutputExternalField
MappingInput[]
fieldsMapping
54.0RequiredThe name of hyper file.StringhyperFileName
51.0RequiredThe object name.Stringobject
51.0RequiredThe output external operation type. Valid
values are:
RecipeOutput
ExternalOperation
operation
## •
## Empty
## •
## Insert
## •
## Update
## •
## Upsert
65.0OptionalA map of key/value pairs of a named
credential for a virtual private connection
## (VPC).
Map<String,String>named
## Credential
## Pivot Input
A pivot for an aggregate data node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe source for the pivot.Stringsource
51.0RequiredThe list of values for the pivot.String[]values
## Pivot V2 Input
A version 2 pivot for an aggregate data node in a recipe.
## 62
Pivot InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe map of the pivot fields information.Map<RecipeName
LabelInput, List
pivotFields
## Info
54.0RequiredThe list of source fields for the pivot.String[]sourceFields
54.0RequiredThe list of value combinations for the pivot.String[]value
## Combinations
## Predict Values Field Input
A field for a predict values node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe label for the field.Stringlabel
51.0RequiredThe name for the field.Stringname
51.0RequiredThe setup for the field.PredictValuesSetup
## Input[]
prediction
## Setup
## Predict Values Input Field Input
An input field for a predict values node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe field name.Stringname
## Predict Values Node Input
A predict missing values node in a recipe.
## 63
Predict Values Field InputRecipe REST API Request Bodies

## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.PredictValues
ParametersInput
parameters
## Predict Values Parameters Input
The parameters for a predict values node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of fields.PredictValuesField
## Input[]
fields
## Predict Values Setup Input
The setup for a predict values node field.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of input fields for the model.PredictValuesInput
FieldInput[]
modelInput
## Fields
51.0RequiredThe source field.PredictValuesInput
FieldInput
sourceField
## Recipe Configuration Collection Input
A collection of data prep recipe configurations.
## 64
Predict Values Parameters InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe list of recipe configurations to update.RecipeConfiguration
CollectionInput[]
recipe
## Configurations
## Recipe Configuration Fiscal Input
The data prep recipe fiscal configuration data.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe first day of week, calendar and fiscal.IntegerfirstDayOf
## Week
54.0RequiredThe recipe configuration fiscal type. Valid
values are:
RecipeConfiguration
TypeEnum
fiscalType
## •
Offset (Recipe Configuration Fiscal
## Offset Input)
54.0RequiredIndicates whether this recipe configuration
is the default configuration (true) or not
## (false).
BooleanisDefault
## Recipe Configuration Fiscal Offset Input
The data prep recipe fiscal offset configuration data.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe ID of the recipe configuration.Stringid
54.0RequiredThe month offset.StringmonthOffset
54.0RequiredThe fiscal offset year based on for the recipe
configuration. Valid values are:
RecipeConfiguration
FiscalOffsetYear
BasedOnEnum
yearBasedOn
## •
## End
## 65
Recipe Configuration Fiscal InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
## Start
## Recipe Configuration
A data prep recipe configuration.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe recipe configuration fiscal type. Valid
values are:
RecipeConfiguration
TypeEnum
fiscalType
## •
Fiscal (Recipe Configuration Fiscal
## Input)
54.0RequiredIndicates whether this recipe configuration
is the default configuration (true) or not
## (false).
BooleanisDefault
## Recipe Conversion Detail Input
The details for the upconversion of a data prep recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe conversion detail ID.Integerconversion
DetailId
52.0RequiredThe conversion detail message.Stringmessage
52.0RequiredThe name of the node referenced in the
conversion detail.
StringnodeName
52.0Small, 52.0The severity of the conversion detail. Valid
values are:
ConnectRecipe
ConversionSeverity
## Enum
severity
## •
UserInfo
## •
## Warning
## 66
Recipe ConfigurationRecipe REST API Request Bodies

## Recipe Definition Input
The definition for a data prep recipe. Available on for R3 recipes.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe recipe definition name.Stringname
49.0RequiredThe map of recipe nodes by name. Valid
values are:
Map<String, Recipe
NodeInput>
nodes
## •
## Aggregate Node
## •
## Append Node Input
## •
## Append V2 Node Input
## •
## Bucket Node Input
## •
## Bucket V@ Node Input
## •
## Cluster Node Input
## •
## Compute Relative Node Input
## •
## Detect Sentiment Node Input
## •
## Discovery Node Input
## •
## Export Node Input
## •
## Extension Node Input
## •
## Extract Grain Node Input
## •
## Filter Node Input
## •
## Flatten Node Input
## •
## Format Date Node Input
## •
## Formula Node Input
## •
## Join Node Input
## •
## Load Node Input
## •
## Optimized Append Node Input
## •
## Optimized Update Node Input
## •
## Output D360 Node Input
## •
## Output Data Cloud Node Input
## •
## Output External Node Input
## •
## Predict Values Node Input
## •
## Recommendation Node Input
## •
## Save Node Input
## •
## Schema Node Input
## 67
Recipe Definition InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
## Split Node Input
## •
SQL Filter Node Input
## •
## Time Series Node Input
## •
## Time Series V2 Node Input
## •
## Typecast Node Input
## •
## Update Node Input
57.0RequiredThe recipe run mode. Valid values are:RecipeRunModerunMode
## •
## Full
## •
## Incremental
## •
## Streaming
49.0RequiredThe recipe definition version.Stringversion
49.0RequiredThe recipe definition UI metadata.Objectui
## Recipe Input
A data prep recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe list of conversion details when
converting the recipe to R3 that are saved.
RecipeConversion
DetailInput[]
conversion
## Details
38.0OptionalThe recipe's definition.Stringdataflow
## Definition
41.0OptionalThe recipe's execution engine. Valid values
are:
ConnectRecipe
ExecutionEngine
## Enum
execution
## Engine
## •
## V1
## •
## V2
38.0Required for POST
and PATCH
The recipe's JSON file content (see
/wave/recipes/<recipeId>/file for more
information). This property is internal to the
StringfileContent
recipe UI and is available for debugging and
reference purposes only. This property is
valid only for Data Prep Classic recipes.
## 68
Recipe InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
38.0Required when
dataflow
The Analytics app the recipe is published in.AssetReferenceInputfolder
Definition is
present
48.0RequiredSpecifies the format of the recipe. Valid
values are:
ConnectRecipe
FormatTypeEnum
format
## •
R2 (Data Prep Classic)
## •
R3 (Data Prep)
51.0OptionalA history label to tag the version of the
recipe.
StringhistoryLabel
38.0OptionalA short label for the recipe.Stringlabel
51.0OptionalThe recipe license type and other properties.Licenses
## Attributes
## Input
license
## Attributes
42.0OptionalThe target format or system to publish the
recipe to. Valid values are:
ConnectRecipe
PublishingTarget
## Enum
publishing
## Target
## •
Dataset (Publish to Dataset)
49.0OptionalThe recipe definition for the Data Prep
recipe only. This property isn’t supported
for Data Prep Classic recipes.
RecipeDefinition
## Input
recipe
## Definition
38.0OptionalThe security predicate of the target dataset.StringrowLevel
## Security
## Predicate
38.0OptionalThe recipe's schedule dataflow run.Stringschedule
51.0OptionalThe source dataflow asset used to upconvert
to the recipe to R3.
AssetReferenceInputsource
## Dataflow
## Recipe Name Label Input
The name and label for a field in a recipe node.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe label of the field.Stringlabel
## 69
Recipe Name Label InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe name of the field.Stringname
54.0RequiredThe list of value combinations for the pivot.String[]value
## Combinations
## Recipe Node Input
The base node for a recipe.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Inherited by Aggregate Node, Append Node Input, Append V2 Node Input, Bucket Node Input, Bucket V2 Node Input, Cluster Node
Input, Compute Relative Node Input, Detect Sentiment Node Input, Discovery Node Input, Export Node Input, Extension Node Input,
Extract Grain Node Input, Filter Node Input, Flatten Node Input, Format Date Node Input, Formula Node Input, Join Node Input, Load
Node Input, Optimized Append Node Input, Optimized Update Node Input, Output D360 Node Input, Output Data Cloud Node Input,
Output External Node Input, Predict Values Node Input, Recommendation Node Input, Save Node Input, Schema Node Input, Split Node
Input, SQL Filter Node Input, Time Series Node Input, Time Series V2 Node Input, Typecast Node Input, Update Node Inputand Update
## Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe recipe node action. Valid recipe actions
are:
RecipeNodeActionaction
## •
## Aggregate
## •
## Append
## •
Append_V2
## •
## Bucket
## •
BucketV2
## •
## Clustering
## •
ComputeRelative
## •
DateFormatConversion
## •
DetectSentiment
## •
DiscoveryPredict
## •
## Export
## •
## Extension
## •
## Extract
## •
## Filter
## •
## Flatten
## 70
Recipe Node InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
## Formula
## •
## Join
## •
## Load
## •
OptimizedAppendOutput
## •
OptimizedUpdateOutput
## •
OutputD360
## •
OutputExternal
## •
PredictMissingValues
## •
## Recommendation
## •
## Save
## •
## Schema
## •
## Split
## •
SqlFilter
## •
TimeSeries
## •
TimeSeriesV2
## •
TypeCast
## •
## Updatei
## •
UpdateDataCloudObject
## •
WriteDataCloudObject
51.0RequiredThe schema changes for the node.SchemaNodeInputschema
51.0RequiredThe source node ids.String[]sources
## Recipe Notification Input
A notification for a data prep recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0OptionalThe number of minutes that a recipe can
run before sending an alert.
IntegerlongRunning
AlertInMins
49.0RequiredValid types of email notification levels. Valid
values are:
ConnectEmail
NotificationLevel
## Enum
notification
## Level
## •
## Always
## •
## Failures
## 71
Recipe Notification InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
## Never
## •
## Warnings
## Recipe Type Name Input
The name and type for a field in a recipe node.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe name of the field.Stringname
49.0RequiredThe type of the field.Stringtype
## Recommendation Node Input
A recommendation node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredThe parameters for the node.Recommendation
ParametersInput
parameters
## Recommendation Parameters Input
The parameters for a recommendation node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredThe customer ID field.StringcustIdField
## 72
Recipe Type Name InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredIndicates whether to exclude previous
recommendations (true) or not (false).
## Booleanexclude
## Previous
## Recommendations
53.0RequiredThe product ID field.StringproductId
## Field
53.0RequiredThe product recommendations field.Integerproduct
## Recommendations
53.0RequiredThe rating field.StringratingField
53.0RequiredThe target field.RecipeNameLabel
## Input
targetField
53.0RequiredThe target rank field.RecipeNameLabel
## Input
targetRank
## Field
53.0RequiredThe target rating field.RecipeNameLabel
## Input
targetRating
## Field
53.0RequiredIndicates whether to use implicit ratings
(true) or not (false).
BooleanuseImplicit
## Ratings
## Sample Parameters Input
The sample parameters for loading data.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
55.0RequiredThe sample filters.FilterParameters
## Input
filters
55.0RequiredA list of fields to sort sample.String[]sortBy
55.0RequiredThe sample sort direction. Valid values are:RecipeSortOrder
## Enum
sortDirection
## •
## Ascending
## •
## Descending
55.0RequiredThe recipe sample type. Valid values are:SampleTypesampleType
## •
## Custom
## •
## Random
## •
TopN
## 73
Sample Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
## Unique
55.0RequiredThe field name for a unique sample.StringuniqueSample
FieldName
## Streaming Parameters Input
The streaming parameters for loading data.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
57.0RequiredThe output mode. Valid values are:OutputModeEnumoutputMode
## •
## Append
## •
## Complete
## •
## Update
57.0RequiredThe trigger interval in seconds.Integertrigger
IntervalSec
55.0RequiredThe trigger type. Valid values are:TriggerTypeEnumtriggerType
## •
## Fixed
## Save Dataset Input
The dataset for a save node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe analytics folder for the dataset.StringfolderName
53.0RequiredIndicates whether the data is staged (true)
or not (false).
BooleanisStaged
51.0RequiredThe label for the dataset.Stringlabel
51.0RequiredThe name of the dataset.Stringname
## 74
Streaming Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe security predicate.StringrowLevel
## Security
## Filter
51.0RequiredThe sobject security sharing source.StringrowLevel
SharingSource
51.0RequiredThe type of the dataset.Stringtype
## Save Node Input
A save data node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe parameters for the node.SaveParametersInputparameters
## Save Parameters Input
The parameters for a save node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe dataset to save.SaveDatasetInputdataset
55.0RequiredThe date configuration name.Stringdate
## Configuration
## Name
51.0RequiredThe list of fields to save.String[]fields
56.0RequiredA list of the measures to currencies.MeasureToCurrency
## Input[]
measuresTo
## Currencies
## 75
Save Node InputRecipe REST API Request Bodies

## Schema Field Format Symbols Input
The field format symbols for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe currency symbol format.Stringcurrency
## Symbol
51.0OptionalThe decimal symbol format.StringdecimalSymbol
51.0OptionalThe grouping symbol format.Stringgrouping
## Symbol
## Schema Field Parameters Input
The field parameters for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0OptionalThe value to output on error.StringerrorValue
51.0RequiredThe schema field name.Stringname
51.0RequiredThe schema field properties.SchemaField
PropertiesInput
newProperties
## Schema Field Properties Input
The field properties for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe new schema field property label.Stringlabel
51.0RequiredThe new schema field property name.Stringname
## 76
Schema Field Format Symbols InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe new schema type property type values.SchemaFieldType
PropertiesInput
type
## Properties
## Schema Field Type Properties Input
The field type properties for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe DateTime format.Stringformat
51.0RequiredThe total length of the text.Integerlength
51.0OptionalThe length of an arbitrary precision value.Integerprecision
51.0OptionalThe number of digits to the right of the
decimal point.
## Integerscale
51.0OptionalThe number format.SchemaFieldFormat
SymbolsInput
symbols
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Schema Node Input
A schema node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
## 77
Schema Field Type Properties InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe schema fields for the node.SchemaParameters
## Input[]
fields
## Schema Parameters Input
The parameters for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe schema fields for the node.SchemaField
ParametersInput
## Representation[]
fields
51.0RequiredThe schema slice definition for the node.SchemaSliceInputslice
## Schema Slice Input
The slice definition for a schema node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of fields for SELECT or DROP.String[]fields
51.0RequiredIndicates whether the node action ignores
missing fields (true) or not (false).
BooleanignoreMissing
## Fields
51.0RequiredThe slice mode. Valid values are:RecipeSliceModemode
## •
## SELECT
## •
## DROP
## Split Node Input
A split node in a recipe.
## 78
Schema Parameters InputRecipe REST API Request Bodies

## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
49.0RequiredThe parameters for the node.SplitParametersInputparameters
## Split Parameters Input
The parameters for a split node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe split delimiter.Stringdelimiter
51.0RequiredThe source field.StringsourceField
51.0RequiredThe list of target fields.RecipeNameLabel
## Input[]
targetFields
SQL Filter Node Input
A SQL filter node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredThe parameters for the node.SQLFilterParameters
## Input
parameters
SQL Filter Parameters Input
The parameters for a SQL filter node in a recipe.
## 79
Split Parameters InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
53.0RequiredThe SQL filter expression.StringsqlFilter
## Expression
SQL Formula Date Only Field Input
The SQL formula date only field for a recipe node.
## Properties
Inherits properties from SQL Formula Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe default value for the date field.StringdefaultValue
51.0RequiredThe format for the date field.Stringformat
SQL Formula Date Time Field Input
The SQL formula date time field for a recipe node.
## Properties
Inherits properties from SQL Formula Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe default value for the date field.StringdefaultValue
51.0RequiredThe format for the date field.Stringformat
SQL Formula Field Input
The base SQL formula field for a recipe node.
## 80
SQL Formula Date Only Field InputRecipe REST API Request Bodies

## Properties
Inherited by SQL Formula Date Only Field Input, SQL Formula Date Time Field Input, SQL Formula Multivalue Field Input, SQL Formula
Numeric Field Input, and SQL Formula Text Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe formula expressionStringformula
## Expression
51.0RequiredThe formula label.Stringlabel
51.0RequiredThe formula name.Stringname
51.0RequiredThe recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
SQL Formula Parameters Input
The SQL formula parameters for a formula.
## Properties
Inherits properties from Formula Parameters Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of formula fields. Valid values are:SqlFormulaField
## Input[]
fields
## •
SQL Formula Date Only Field Input
## •
SQL Formula Date Time Field Input
## •
SQL Formula Multivalue Field Input
## •
SQL Formula Numeric Field Input
## •
SQL Formula Text Field Input
SQL Formula Multivalue Field Input
The SQL formula multivalue field for a recipe node.
## 81
SQL Formula Parameters InputRecipe REST API Request Bodies

## Properties
Inherits properties from SQL Formula Field Input.
SQL Formula Numeric Field Input
The SQL formula numeric field for a recipe node.
## Properties
Inherits properties from SQL Formula Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe default value for the numeric field.StringdefaultValue
51.0RequiredThe precision of the numeric field.Integerprecision
51.0RequiredThe scale of the numeric field.Integerscale
SQL Formula Text Field Input
The SQL formula text field for a recipe node.
## Properties
Inherits properties from SQL Formula Field Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0OptionalThe default value for the text field.StringdefaultValue
51.0RequiredThe precision of the text field.Integerprecision
## Target Field Input
A target field for a recipe bucket.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredThe label for the field.Stringlabel
## 82
SQL Formula Numeric Field InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
64.0RequiredThe name for the field.Stringname
64.0RequiredThe data type. Valid recipe data types are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Time Series Input Confidence Interval High Low
A confidence interval for a time series recipe node.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe high confidence interval.RecipeNameLabel
## Input
high
52.0RequiredThe low confidence interval.RecipeNameLabel
## Input
low
## Time Series Node Input
A time series node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe parameters for the node.TimeSeries
ParametersInput
parameters
## 83
Time Series Input Confidence Interval High LowRecipe REST API Request Bodies

## Time Series Parameters Input
The parameters for a time series node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe confidence interval. Valid values are:RecipeTimeSeries
ConfidenceInterval
## Type
confidence
## Interval
## •
## Eighty
## •
NinetyFive
## •
## None
52.0RequiredThe confidence interval field name and
labels.
Map<String, Time
SeriesInput
ConfidenceInterval
HighLow>
confidence
## Interval
## Fields
51.0RequiredThe day field.StringdayField
51.0RequiredThe list of forecast fields.String[]forecast
## Fields
51.0RequiredThe forecast length.Integerforecast
## Length
51.0RequiredThe value to group dates by. Valid values
are:
RecipeGroupDatesBygroupDatesBy
## •
## Year
## •
YearMonth
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
51.0RequiredIndicates whether to ignore the last time
period (true) or not (false).
BooleanignoreLast
TimePeriod
51.0RequiredThe time series model. Valid values are:RecipeTimeSeries
## Model
model
## •
## Additive
## •
## Auto
## •
## Multiplicative
51.0RequiredThe seasonality.Integerseasonality
51.0RequiredThe sub year field.StringsubYearField
## 84
Time Series Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe target date field.RecipeNameLabel
## Input
targetDate
## Field
51.0RequiredThe list of target forecast fields.RecipeNameLabel
## Input[]
target
## Forecast
## Fields
51.0RequiredThe year field.StringyearField
## Time Series V2 Algorithm Input
The algorithm for a time series version 2 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe time series model. Valid values are:RecipeTimeSeries
## Model
model
## •
## Additive
## •
## Auto
## •
## Multiplicative
54.0RequiredThe seasonality value.Integerseasonality
## Time Series V2 Forecast Info Input
The forecast info for a time series version 2 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe aggregate data.AggregateInputaggregate
54.0RequiredThe confidence interval field name and
labels.
TimeSeriesOutput
ConfidenceInterval
HighLow
confidence
## Interval
## Fields
54.0Small, v54.0The aggregate data.RecipeNameLabel
## Input
forecastField
## 85
Time Series V2 Algorithm InputRecipe REST API Request Bodies

## Time Series V2 Node Input
A time series version 2 node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe parameters for the node.TimeSeriesV2
ParametersInput
parameters
## Time Series V2 Parameters Input
The parameters for a time series version 2 node in a recipe.
## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe forecast algorithm. Valid values are:TimeSeriesV2
ForecastAlgorithm
## Enum
algorithm
## •
HoltWinters
54.0RequiredThe parameters for the algorithm.TimeSeriesV2
AlgorithmInput
algorithm
## Parameters
54.0RequiredThe confidence interval. Valid values are:RecipeTimeSeries
ConfidenceInterval
## Type
confidence
## Interval
## •
## Eighty
## •
NinetyFive
## •
## None
54.0RequiredThe forecast date field.StringforecastDate
## Field
54.0RequiredThe value to group dates by. Valid values
are:
RecipeGroupDatesByforecastDates
## By
## •
FiscalYear
## •
FiscalYearMonth
## •
FiscalYearQuarter
## •
FiscalYearWeek
## •
YearMonth
## 86
Time Series V2 Node InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
54.0RequiredThe list of forecast fields.TimeSeriesV2
ForecastInfoInput[]
forecast
## Fields
54.0RequiredThe forecast length.Integerforecast
## Length
54.0RequiredThe forecast length type. Valid values are:TimeSeriesV2
ForecastLengthType
## Enum
forecast
LengthType
## •
## Rolling
54.0RequiredThe list of grouping fields.ExtractGrain
ParameterInput[]
grouping
## Fields
54.0RequiredThe partial data handling value. Valid values
are:
TimeSeriesV2Partial
DataHandlingEnum
partialData
## Handling
## •
IgnoreLast
## •
## None
54.0RequiredThe target date field.RecipeNameLabel
## Input
targetDate
## Field
## Typecast Node Input
A typecast node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.TypecastParameters
## Input
parameters
## Typecast Parameters Input
The parameters for a typecast node in a recipe.
## 87
Typecast Node InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe list of fields to typecast.SchemaField
ParametersInput[]
fields
## Typographic Cluster Input
The configuration for a typographic cluster algorithm.
## Properties
Inherits properties from AbstractBucketAlgorithmtInput.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
52.0RequiredThe edit distanceIntegerdistance
## Threshold
52.0RequiredIndicates whether to ignore case (true) or
not (false).
BooleanignoreCase
## Update Data Cloud Object Node Input
A Data 360 object update node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
66.0RequiredThe parameters for the node.UpdateDataCloud
ObjectParameters
## Input
parameters
## Update Data Cloud Object Parameters Input
The parameters for an update data cloud object node in a recipe.
## 88
Typographic Cluster InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
66.0RequiredThe connector type. Valid values are:ConnectWaveData
ConnectorTypeEnum
connectorType
## •
AmazonAthena
## •
AmazonRedshiftOutput
## •
AmazonS3
## •
AmazonS3Output
## •
AmazonS3Private
## •
AwsRdsAuroraMySQL
## •
AwsRdsAuroraPostgres
## •
AwsRdsMariaDB
## •
AwsRdsMySQL
## •
AwsRdsPostgres
## •
AwsRdsSqlServer
## •
AzureDataLakeGen2Output
## •
AzureSqlDatabase
## •
AzureSqlDatawarehouse
## •
Databricks(Beta)
## •
GoogleAnalytics4
## •
GoogleBigQuery
## •
GoogleBigQueryDirect
## •
GoogleBigQueryStandardSQL
## •
GoogleSpanner
## •
HerokuPostgres
## •
HubSpot
## •
MarketoV2
## •
NetSuite
## •
OracleEloqua
## •
## Redshift
## •
RedshiftPrivate
## •
SalesforceExternal
## •
SalesforceMarketingCloud
OAuth2
## •
SapHanaCloud
## •
SfdcLocal
## •
SnowflakeComputing
## •
SnowflakeDirect
## •
SnowflakeOutput
## 89
Update Data Cloud Object Parameters InputRecipe REST API Request Bodies

Available VersionRequired or
## Optional
DescriptionTypeProperty Name
## •
SnowflakePrivate
## •
SnowflakePrivateOutput
## •
TableauOnline
## •
TableauHyperOutput
## •
## Zendesk
66.0RequiredThe list of the Data 360 field mappings.List[ OutputData
CloudFields
## Mapping]
fieldMappings
66.0RequiredThe name of the Data 360 object to update.Stringname
66.0RequiredThe update operation. Valid values are:OperationEnumoperation
## •
## Append
## •
## Delete
## •
## Upsert
66.0RequiredThe name of the primary key field.StringprimaryKey
66.0RequiredThe output type. Valid values are:RecipeDataCloud
OutputTypeEnum
type
## •
DateLakeObject
## \
## Update Node Input
An update node in a recipe.
## Properties
Inherits properties from Recipe Node Input.
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
51.0RequiredThe parameters for the node.UpdateParameters
## Input
parameters
## Update Parameters Input
The parameters for an update node in a recipe.
## 90
Update Node InputRecipe REST API Request Bodies

## Properties
Available VersionRequired or
## Optional
DescriptionTypeProperty Name
54.0RequiredThe list of left keys.String[]leftKeys
54.0RequiredThe right of left keys.String[]rightKeys
54.0RequiredThe map of columns to update.Map<String, String>updateColumns
## 91
Update Parameters InputRecipe REST API Request Bodies

## RECIPE REST API RESPONSE BODIES
The successful execution of a request to a Recipe REST API resource can return a response body in either JSON or XML format.
A request to a Recipe REST API resource always returns an HTTP response code, whether the request was successful or not.
## Abstract Bucket Algorithm
The base bucket algorithm for a recipe.
## Aggregate
The aggregate data for a recipe node.
## Aggregate Node
An aggregate data node in a recipe.
## Aggregate Parameters
The parameters for an aggregate data node in a recipe.
## Append Mapping
A field mapping for an append node in a recipe.
## Append Node
An append node in a recipe.
## Append Parameters
The parameters for an append node in a recipe.
AppendV2 Node
A version 2 append node in a recipe.
## Bucket Date Argument
A date bucket argument for a recipe.
## Bucket Date Bucket
A date bucket field for a recipe.
## Bucket Dimension Bucket
A dimension bucket field for a recipe.
## Bucket Field
A field for a bucket node in a recipe.
## Bucket Measure Bucket
A date bucket field for a recipe.
## Bucket Node
A bucket node in a recipe.
## Bucket Parameters
The parameters for a bucket node in a recipe.
## Bucket Setup
The setup for a bucket node field in a recipe.
## 92

## Bucket Source Field
The source field for a bucket node in a recipe.
## Bucket V2
A version 2 bucket in a recipe.
## Bucket Term
A bucket term in a recipe node.
## Bucket V2 Node
A version 2 bucket node in a recipe, with improved functionality.
## Bucket V2 Parameters
A paramters for a version 2 bucket node in a recipe.
## Bucket
The base bucket for a recipe.
## Cluster Node
A cluster node in a recipe.
## Cluster Parameters
The parameters for a cluster node in a recipe.
## Compute Relative Node
A compute relative node in a recipe.
## Compute Relative Parameters
The parameters for a compute relative node in a recipe.
## Compute Relative Sort Parameters
The sort direction parameters for a compute relative node in a recipe.
## Data Object Category
The data object category for an Output Data Cloud node.
## Detect Sentiment Node
A detect sentiment node in a recipe.
## Detect Sentiment Parameters
The parameters for a detect sentiment node in a recipe.
## Discovery Contributor
The discovery information for an Einstein Discovery prediction field.
## Discovery Node
An Einstein Discovery predict node in a recipe.
## Discovery Parameters
The parameters for an Einstein Discovery predict node in a recipe.
## Discovery Source
The discovery information for an Einstein Discovery source field.
## Export Limits
The limits for an export node in a recipe.
## Export Node
An export node in a recipe.
## 93
Recipe REST API Response Bodies

## Export Parameters
The parameters for an export node in a recipe.
## Extension Node
An extension node in a recipe.
## Extension Parameters
The parameters for an extension node in a recipe.
## Extract Field
An extract grain field.
## Extract Node
An extract grain node in a recipe.
## Extract Parameter
A parameter for an extract grain field.
## Extract Parameters
The parameters for an extract grain node in a recipe.
## Filter Expression
A regex expression for a filter.
## Filter Node
A filter node in a recipe.
## Filter Parameters
The parameters for a filter node in a recipe.
## Flatten Field
A field for a flatten node in a recipe.
## Flatten Node
A flatten node in a recipe.
## Flatten Parameters
The parameters for a flatten node in a recipe.
## Format Date Node
A date format conversion node in a recipe.
## Format Date Parameters
The parameters for a date format conversion node in a recipe.
## Format Date Pattern
The pattern for a date format conversion.
## Formula Node
A formula node in a recipe.
## Formula Parameters
The parameters for a formula node in a recipe.
## Join Node
A join node in a recipe.
## Join Parameters
The parameters for a join node in a recipe.
## 94
Recipe REST API Response Bodies

## Load Analytics Dataset
A CRM Analytics dataset for a load node in a recipe.
## Load Connected Dataset
A connected dataset for a load node in a recipe.
## Load Data Lake Object
A data lake object for a load node in a recipe.
## Load Data Model Object
A data model object for a load node in a recipe.
## Load Dataset
The base dataset for a load node in a recipe.
## Load Node
A load node in a recipe.
## Load Parameters
The parameters for a load node in a recipe.
## Legacy Formula Field
A legacy formula field for a formula.
## Legacy Formula Parameters
The legacy formula parameters for a formula.
## Measure To Currency
The conversion information for currency measure field.
## Optimized Append Node
An optimized append node in a recipe.
## Optimized Append Parameters
The parameters for an optimized append node in a recipe.
## Optimized Update Node
An optimized update node in a recipe.
## Optimized Update Parameters
The parameters for an optimized update node in a recipe.
## Output D360 Fields Mapping
The fields mapping for an output D360 node in a recipe.
## Output D360 Node
An output D360 node in a recipe.
## Output D360 Parameters
The parameters for an output D360 node in a recipe.
## Output Data Cloud Fields Mapping
The fields mapping for an output Data 360 node in a recipe.
## Output Data Cloud Node
An output node in a recipe to write to Data 360.
## Output Data Cloud Parameters
The parameters for an output Data 360 node in a recipe.
## 95
Recipe REST API Response Bodies

## Output External Field Mapping
A field mapping for an output external node in a recipe.
## Output External Node
An output external node in a recipe.
## Output External Parameters
The parameters for an output external node in a recipe.
## Pivot
A pivot for an aggregate data node in a recipe.
PivotV2
A version 2 pivot for an aggregate data node in a recipe.
## Predict Values Field
A field for a predict values node in a recipe.
## Predict Values Input Field
An input field for a predict values node in a recipe.
## Predict Values Node
A predict missing values node in a recipe.
## Predict Values Parameters
The parameters for a predict values node in a recipe.
## Predict Values Setup
The setup for a predict values node field.
## Recipe Collection
A collection of data prep recipes.
## Recipe Configuration Collection
A collection of data prep recipe configurations.
## Recipe Configuration Fiscal
The data prep recipe fiscal configuration data.
## Recipe Configuration Fiscal Offset
The data prep recipe fiscal offset configuration data.
## Recipe Configuration
The data prep recipe configuration data.
## Recipe Conversion Detail
The details for the upconversion of a data prep recipe.
## Recipe Definition
The definition for a data prep recipe. Available on for R3 recipes.
## Recipe Name Label
The name and label for a field in a recipe node.
## Recipe Node
The base node for a recipe.
## Recipe Notification
A notification for a data prep recipe.
## 96
Recipe REST API Response Bodies

## Recipe Validation Detail
The validation details for a data prep recipe.
## Recipe
A data prep recipe.
## Recommendation Node
A recommendation node in a recipe.
## Recommendation Parameters
The parameters for a recommendation node in a recipe.
## Sample Parameters
The sample parameters for loading data.
## Save Dataset
The dataset for a save node in a recipe.
## Save Node
A save data node in a recipe.
## Save Parameters
The parameters for a save node in a recipe.
## Schema Field Format Symbols
The field format symbols for a schema node in a recipe.
## Schema Field
The field for a schema node in a recipe.
## Schema Field New Properties
The new field properties for a schema node in a recipe.
## Schema Field Type Properties
The field type properties for a schema node in a recipe.
## Schema Node
A schema node in a recipe.
## Schema Parameters
The parameters for a schema node in a recipe.
## Schema Slice
The slice definition for a schema node in a recipe.
## Split Node
A split node in a recipe.
## Split Parameters
The parameters for a split node in a recipe.
SQL Filter Node
A SQL filter node in a recipe.
SQL Filter Parameters
The parameters for a SQL filter node in a recipe.
SQL Formula Date Field
The SQL formula date field for a recipe node.
## 97
Recipe REST API Response Bodies

SQL Formula Field
The base SQL formula field for a recipe node.
SQL Formula Parameters
The SQL formula parameters for a formula.
SQL Formula Multivalue Field
The SQL formula multivalue field for a recipe node.
SQL Formula Numeric Field
The SQL formula numeric field for a recipe node.
SQL Formula Text Field
The SQL formula text field for a recipe node.
## Streaming Parameters
The streaming parameters for data output.
## Target Field
A target field for a recipe bucket.
## Time Series Node
A time series node in a recipe.
## Time Series Output Confidence Interval High Low
A confidence interval for a time series recipe node.
## Time Series Parameters
The parameters for a time series node in a recipe.
## Time Series V2 Algorithm Parameters
The algorithm parameters for a time series version 2 node in a recipe.
## Time Series V2 Forecast Info
The forecast information for a time series version 2 node in a recipe.
## Time Series V2 Node
A time series version 2 node in a recipe.
## Time Series V2 Parameters
The parameters for a time series version 2 node in a recipe.
## Typecast Node
A typecast node in a recipe.
## Typecast Parameters
The parameters for a typecast node in a recipe.
## Typographic Cluster
The configuration for a typographic cluster algorithm.
## Update Data Cloud Object Node
A Data 360 object update node in a recipe.
## Update Data Cloud Object Parameters
The parameters for an update data cloud object node in a recipe.
## Update Node
An update node in a recipe.
## 98
Recipe REST API Response Bodies

## Update Parameters
The parameters for an update node in a recipe.
## Abstract Bucket Algorithm
The base bucket algorithm for a recipe.
## Properties
Inherited by Typographic Cluster.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The algorithm type of the recipe bucket
field. Valid values are:
RecipeBucket
AlgorithmType
type
## •
TypographicClustering
## Aggregate
The aggregate data for a recipe node.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The recipe aggregation type. Valid values
are:
RecipeAggregate
## Type
action
## •
## Avg
## •
## Count
## •
## Maximum
## •
## Median
## •
## Minimum
## •
StdDev
## •
StdDevP
## •
## Sum
## •
## Unique
## •
## Var
## •
VarP
51.0Small, v51.0The label for the aggregate data.Stringlabel
## 99
Abstract Bucket AlgorithmRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The name for the aggregate data.Stringname
51.0Small, v51.0The source for the aggregate data.Stringsource
## Aggregate Node
An aggregate data node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The parameters for the node.Aggregate
## Parameters
parameters
## Aggregate Parameters
The parameters for an aggregate data node in a recipe.
## Properties
## Available
## Version
## Filter Group
and Version
DescriptionTypeProperty
## Name
51.0Small, v51.0The list of aggregations for the node.Aggregate[]aggregations
51.0Small, v51.0The list of groupings for the node.String[]groupings
53.0Small, v53.0The aggregate type for the node.
Valid values are:
RecipeAggregate
NodeEnum
nodeType
## •
## Hierarchical
## •
## Standard
53.0Small, v53.0The parent field for the nodeStringparentField
53.0Small, v53.0The percentage field for the nodeStringpercentage
## Field
54.0Small, v54.0The pivot v2 data for the node.PivotV2[]pivot_v2
51.0Small, v51.0The list of pivots for the node.Pivot[]pivots
## 100
Aggregate NodeRecipe REST API Response Bodies

## Available
## Version
## Filter Group
and Version
DescriptionTypeProperty
## Name
53.0Small, v53.0The self field for the nodeStringselfField
## Append Mapping
A field mapping for an append node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The bottom dataset field.Stringbottom
51.0Small, v51.0The top dataset field.Stringtop
## Append Node
An append node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The parameters for the node.AppendParametersparameters
## Append Parameters
The parameters for an append node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
55.0Small, v55.0Indicates whether disjoint schema merge is
allowed when automatically mapping fields
(true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
## 101
Append MappingRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of mappings for the node.AppendMapping[]fieldMappings
AppendV2 Node
A version 2 append node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The parameters for the node.AppendParametersparameters
## Bucket Date Argument
A date bucket argument for a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The date argument.Longargument
49.0Small, 49.0The recipe bucket date grain type. Valid
values are:
RecipeBucketGraintype
## •
AbsoluteDate
## •
## Days
## •
FiscalQuarters
## •
FiscalYears
## •
## Months
## •
## Quarters
## •
## Weeks
## •
## Years
## 102
AppendV2 NodeRecipe REST API Response Bodies

## Bucket Date Bucket
A date bucket field for a recipe.
## Properties
Inherits properties from Bucket.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The date range end.BucketDate
## Argument
rangeEnd
49.0Small, 49.0The date range start.BucketDate
## Argument
rangeStart
## Bucket Dimension Bucket
A dimension bucket field for a recipe.
## Properties
Inherits properties from Bucket.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The list of source valuesString[]sourceValues
## Bucket Field
A field for a bucket node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The bucket field property label.BucketSetupbucketsSetup
49.0Small, v49.0The bucket field property label.Stringlabel
49.0Small, v49.0The bucket field property name.Stringname
## 103
Bucket Date BucketRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Bucket Measure Bucket
A date bucket field for a recipe.
## Properties
Inherits properties from Bucket.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The range end.DoublerangeEnd
49.0Small, 49.0The range start.DoublerangeStart
## Bucket Node
A bucket node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The parameters for the node.BucketParametersparameters
## Bucket Parameters
The parameters for a bucket node in a recipe.
## 104
Bucket Measure BucketRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The list of fields for the node.BucketField[]fields
## Bucket Setup
The setup for a bucket node field in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0The bucketing algorithm. Valid values are:AbstractBucket
## Algorithm
algorithm
## •
TypographicCluster
51.0Small, v51.0The buckets. Valid values are:Bucketbuckets
## •
BucketDateBucket
## •
BucketDimensionBucket
## •
BucketMeasureBucket
51.0Small, v51.0The default bucket value.StringdefaultBucket
## Value
51.0Small, v51.0Indicates whether pass through is enabled
(true) or not (false).
BooleanisPassThrough
## Enabled
51.0Small, v51.0The null bucket valueStringnullBucket
## Value
51.0Small, v51.0The bucket source fields.BucketSourceFieldsourceField
## Bucket Source Field
The source field for a bucket node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The bucket source field name.Stringname
## 105
Bucket SetupRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Bucket V2
A version 2 bucket in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small 64.0A boolean expression for the bucket.StringbooleanLogic
64.0Small 64.0The list of terms for the bucket.BucketTerm on page
## 106[]
terms
64.0Small 64.0The value for the bucket.Stringvalue
## Bucket Term
A bucket term in a recipe node.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The recipe node data type. Valid recipe data
types are:
RecipeDataTypeopType
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## 106
Bucket V2Recipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0A map of operands for the bucket term.Map<Object,
## Object>
operands
64.0Small, 64.0The operator for the bucket term.Stringoperator
## Bucket V2 Node
A version 2 bucket node in a recipe, with improved functionality.
## Properties
Inherits properties from Recipe Node on page 139.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The parameters for the V2 bucket node.BucketV2Parameters
on page 107
parameters
## Bucket V2 Parameters
A paramters for a version 2 bucket node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The bucket algorithm. Valid bucket
algorithms are:
AbstractBucket
Algorithm on page
## 99[]
algorithm
## •
TypographicCluster on page 158
64.0Small, 64.0A list of the buckets for the node.BucketV2 on page
## 106[]
buckets
64.0Small, 64.0A default bucket for the node.ObjectdefaultBucket
64.0Small, 64.0Indicates whether the bucket result is
multi-value (true) or not (false).
booleanmultiValue
## Result
64.0Small, 64.0A null bucket for the node.ObjectnullBucket
64.0Small, 64.0Indicates whether pass through is enabled
for the bucket (true) or not (false).
booleanpassthrough
## Enabled
## 107
Bucket V2 NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The source field for the bucket.StringsourceField
64.0Small, 64.0The target field for the bucket.TargetField on page
## 153
targetField
## Bucket
The base bucket for a recipe.
## Properties
Inherited by Bucket Date Bucket, Bucket Dimension Bucket, and Bucket Measure Bucket.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The bucket value.Stringvalue
## Cluster Node
A cluster node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.ClusterParametersparameters
## Cluster Parameters
The parameters for a cluster node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The cluster count.IntegerclusterCount
## 108
BucketRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, v53.0Indicates whether to find the optimal
clusters (true) or (not).
BooleanfindOptimal
## Clusters
53.0Small, v53.0Indicates whether to produce scaled
columns (true) or (not).
BooleanproduceScaled
## Columns
53.0Small, v53.0The scaling type. Valid values are:MeasureScalingType
## Enum
scaling
## •
MinMaxScaling
51.0Small, v51.0The source fields.String[]sourceFields
51.0Small, v51.0The target field.RecipeNameLabeltargetField
53.0Small, v53.0A list of target scaled fields.RecipeNameLabel[]targetScaled
## Fields
## Compute Relative Node
A compute relative node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.ComputeRelative
## Parameters
parameters
## Compute Relative Parameters
The parameters for a compute relative node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The formula expression type. Valid values
are:
RecipeFormula
ExpressionType
expression
## Type
## •
## Legacy
## •
## Sql
## 109
Compute Relative NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of formula fields. Valid values are:SqlFormulaField[]fields
## •
SQL Formula Date Field
## •
SQL Formula Multivalue Field
## •
SQL Formula Numeric Field
## •
SQL Formula Text Field
51.0Small, v51.0The list of sort fields.ComputeRelativeSort
## Parameters[]
orderBy
51.0Small, v51.0The list of partition by values.String[]partitionBy
## Compute Relative Sort Parameters
The sort direction parameters for a compute relative node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The sort direction. Valid values are:RecipeSortOrder
## Enum
direction
## •
## Ascending
## •
## Descending
51.0Small, v51.0The field name.StringfieldName
## Data Object Category
The data object category for an Output Data Cloud node.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0The name of the data category.StringcategoryName
60.0Small, 60.0The label of the data category.Stringlabel
## 110
Compute Relative Sort ParametersRecipe REST API Response Bodies

## Detect Sentiment Node
A detect sentiment node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.DetectSentiment
## Parameters
parameters
## Detect Sentiment Parameters
The parameters for a detect sentiment node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The output type. Valid values are:DetectSentiment
OutputTypeEnum
outputType
## •
## Dimension
## •
## Measure
54.0Small, v54.0The sentiment score type. Valid values are:SentimentScoreType
## Enum
sentiment
## Score
## •
## All
## •
## None
51.0Small, v51.0The source field.StringsourceField
51.0Small, v51.0The target field.RecipeNameLabeltargetField
54.0Small, v54.0The collection of target confidence fields.Map<String,
Map<String, Recipe
NameLabel>>
target
## Sentiment
ScoreFields
## Discovery Contributor
The discovery information for an Einstein Discovery prediction field.
## 111
Detect Sentiment NodeRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The discovery field.RecipeNameLabelfield
51.0Small, v51.0The discovery impact.RecipeNameLabelimpact
## Discovery Node
An Einstein Discovery predict node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.DiscoveryParametersparameters
## Discovery Parameters
The parameters for an Einstein Discovery predict node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The map of column mappings.Map<String, String>columnMapping
56.0Small, v56.0The list of multiclass fields.Discovery
## Contributor[]
multiClass
## Fields
51.0Small, v51.0The prediction source.DiscoverySourcepredictSource
51.0Small, v51.0The list of prediction factor fields.Discovery
## Contributor[]
prediction
FactorFields
51.0Small, v51.0The prediction field.RecipeNameLabelprediction
## Field
51.0Small, v51.0The list of prescription fields.Discovery
## Contributor[]
prescription
## Fields
## 112
Discovery NodeRecipe REST API Response Bodies

## Discovery Source
The discovery information for an Einstein Discovery source field.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The name of the source.Stringname
51.0Small, v51.0The type of source.Stringtype
## Export Limits
The limits for an export node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The maximum file size for the export
partition.
IntegermaxFileSizeIn
## Bytes
51.0Small, v51.0The maximum row count for the export
partition.
IntegermaxRowCount
## Export Node
An export node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.ExportParametersparameters
## Export Parameters
The parameters for an export node in a recipe.
## 113
Discovery SourceRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, v53.0The type of the recipe export CSV header
row value. Valid values are:
RecipeExportCsv
HeaderRowValue
## Type
csvHeaderRow
ValueType
## •
FullyQualifiedName
## •
## Label
51.0Small, v51.0The list of fields to select.String[]fields
51.0Small, v51.0The format of the export. Valid values are:RecipeExportFormatformat
## •
## CSV.
51.0Small, v51.0The limits to export.ExportLimitslimitsPerPart
51.0Small, v51.0The user ID with access to the exported
data.
StringuserId
## Extension Node
An extension node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.ExtensionParametersparameters
## Extension Parameters
The parameters for an extension node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0A map of extension arguments, defined by
the extension definition
Map<Object,
## Object>
args
56.0Small, v56.0The name of the extension.Stringname
## 114
Extension NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The namespace of the extension.Stringnamespace
56.0Small, v56.0The version of the extension.Doubleversion
## Extract Field
An extract grain field.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The extract grain type. Valid values are:RecipeDateGraingrainType
## •
## Day
## •
DayEpoch
## •
FiscalMonth
## •
FiscalQuarter
## •
FiscalWeek
## •
FiscalYear
## •
## Hour
## •
## Minute
## •
## Month
## •
## Quarter
## •
## Second
## •
SecondEpoch
## •
## Week
## •
## Year
51.0Small, v51.0The extract field label.Stringlabel
51.0Small, v51.0The extract field name.Stringname
## Extract Node
An extract grain node in a recipe.
## Properties
Inherits properties from Recipe Node.
## 115
Extract FieldRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.ExtractParametersparameters
## Extract Parameter
A parameter for an extract grain field.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The source field.Stringsource
51.0Small, v51.0The list of grain fields.ExtractField[]targets
## Extract Parameters
The parameters for an extract grain node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
55.0Small, v55.0The date configuration name.Stringdate
## Configuration
## Name
51.0Small, v51.0The date fields to extract grains for.ExtractParameter[]grain
## Extractions
## Filter Expression
A regex expression for a filter.
## 116
Extract ParameterRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The field to filter on.Stringfield
51.0Small, v51.0The list of operands.Object[]operands
51.0Small, v51.0The operator to use for the filter.Stringoperator
51.0Small, v51.0The recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Filter Node
A filter node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.FilterParametersparameters
## Filter Parameters
The parameters for a filter node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0The filter boolean logic.StringfilterBoolean
## Logic
51.0Small, v51.0The list of filter expressions.FilterExpression[]filter
## Expressions
## 117
Filter NodeRecipe REST API Response Bodies

## Flatten Field
A field for a flatten node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0Indicates whether the field is a system field
(true) or not (false).
BooleanisSystemField
51.0Small, v51.0The field label.Stringlabel
51.0Small, v51.0The field name.Stringname
## Flatten Node
A flatten node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.FlattenParametersparameters
## Flatten Parameters
The parameters for a flatten node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0Indicates whether to include the self-ID
(true) or not (false)..
BooleanincludeSelfId
51.0Small, v51.0The multi field.FlattenFieldmultiField
51.0Small, v51.0The parent field.StringparentField
51.0Small, v51.0The path field.FlattenFieldpathField
## 118
Flatten FieldRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The self-field.StringselfField
## Format Date Node
A date format conversion node in a recipe.
Inherits properties from Recipe Node.
## Properties
xz
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.FormatDate
## Parameters
parameters
## Format Date Parameters
The parameters for a date format conversion node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The source field.StringsourceField
51.0Small, v51.0The list of source date formats.FormatDatePattern[]sourceFormats
51.0Small, v51.0The target field.RecipeNameLabeltargetField
51.0Small, v51.0The target date format.FormatDatePatterntargetFormat
## Format Date Pattern
The pattern for a date format conversion.
## 119
Format Date NodeRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0A list of values for the construction of the
date format.
## String[]construction
51.0Small, v51.0The list of date format groups.String[]groups
51.0Small, v51.0The regular expression for the date format.Stringregex
## Formula Node
A formula node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.FormulaParametersparameters
## Formula Parameters
The parameters for a formula node in a recipe.
## Properties
Inherited by LegacyFormulaParameters and SqlFormulaParameters.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The forumla expression type. Valid values
are:
RecipeFormula
ExpressionType
expression
## Type
## •
## Legacy
## •
## Sql
## Join Node
A join node in a recipe.
## 120
Formula NodeRecipe REST API Response Bodies

## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.JoinParametersparameters
## Join Parameters
The parameters for a join node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The join type. Valid values are:RecipeJoinTypejoinType
## •
## Cross
## •
## Inner
## •
LeftOuter
## •
## Lookup
## •
MultiValueLookup
## •
## Outer
## •
RightOuter
51.0Small, v51.0The list of left keys.String[]leftKeys
51.0Small, v51.0The left qualifier.StringleftQualifier
51.0Small, v51.0The list of right keys.String[]rightKeys
51.0Small, v51.0The right qualifier.Stringright
## Qualifier
## Load Analytics Dataset
A CRM Analytics dataset for a load node in a recipe.
## Properties
Inherits properties from Load Dataset.
## 121
Join ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The dataset name.Stringname
## Load Connected Dataset
A connected dataset for a load node in a recipe.
## Properties
Inherits properties from Load Dataset.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The name of the connection.Stringconnection
## Name
52.0Small, v52.0The pushdown filter.FilterParametersfilter
65.0Small, v65.0>The mode for accessing connected
datasets. Valid values are:
ConnectedMode
## Enum
mode
## •
## AUTO
## •
## DIRECT
## •
## SYNCED
51.0Small, v51.0The name of the source object.StringsourceObject
## Name
## Load Data Lake Object
A data lake object for a load node in a recipe.
## Properties
Inherits properties from Load Dataset.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The data lake object name.Stringname
## 122
Load Connected DatasetRecipe REST API Response Bodies

## Load Data Model Object
A data model object for a load node in a recipe.
## Properties
Inherits properties from Load Dataset.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The data model object name.Stringname
## Load Dataset
The base dataset for a load node in a recipe.
## Properties
Inherited by Load Analytics Dataset, Load Connected Dataset, Load Data Lake Object, and Load Data Model Object.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The dataset label.Stringlabel
51.0Small, v51.0The type of the dataset. Valid values are:RecipeDatasetTypetype
## •
## Analytics
## •
## Connected
## •
DataLakeObject
## •
DataModelObject
## Load Node
A load node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.LoadParametersparameters
## 123
Load Data Model ObjectRecipe REST API Response Bodies

## Load Parameters
The parameters for a load node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The dataset to load. Valid values are:LoadDatasetdataset
## •
## Load Analytics Dataset
## •
## Load Connected Dataset
## •
## Load Data Lake Object
## •
## Load Data Model Object
51.0Small, v51.0The list of fields to load.String[]fields
65.0Small, v65.0The list of fields to preserve currency for.String[]preserve
## Currency
## Fields
57.0Small, v57.0Indicates whether to purge the cache
(true) or not (false).
BooleanpurgeCache
57.0Small, v57.0The input run mode. Valid values are:InputRunModeEnumrunMode
## •
## Full
## •
## Incremental
## •
## Streaming
55.0Small, v55.0The sample parameters for the dataset load.SampleParameterssampleDetails
51.0Small, v51.0The number of rows to load.IntegersampleSize
## Legacy Formula Field
A legacy formula field for a formula.
## Properties
Inherits properties from Formula Parameters.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The formula expression.Stringformula
## Expression
## 124
Load ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The field label.Stringlabel
51.0Small, 51.0The field name.Stringname
## Legacy Formula Parameters
The legacy formula parameters for a formula.
## Properties
Inherits properties from Formula Parameters.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0RequiredThe list of fields.LegacyFormula
## Field[]
fields
## Measure To Currency
The conversion information for currency measure field.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The conversion rate date field.Stringconversion
RateDateField
56.0Small, v56.0The measure field.StringmeasureField
## Optimized Append Node
An optimized append node in a recipe.
## Properties
Inherits properties from Recipe Node .
## 125
Legacy Formula ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0The parameters for the node.OptimizedAppend
## Parameters
parameters
## Optimized Append Parameters
The parameters for an optimized append node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
62.0Small, 62.0Indicates whether disjoint schema merge is
allowed (true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
62.0Small, 62.0The base dataset to append.LoadAnalytics
## Datatset
dataset
62.0Small, 62.0The name of the date configuration.Stringdate
## Configuration
## Name
## Optimized Update Node
An optimized update node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The parameters for the node.OptimizedUpdate
## Parameters
parameters
## Optimized Update Parameters
The parameters for an optimized update node in a recipe.
## 126
Optimized Append ParametersRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0Indicates whether disjoint schema merge is
allowed (true) or not (false).
BooleanallowImplicit
## Disjoint
## Schema
64.0Small, 64.0The base dataset to update.LoadAnalytics
## Datatset
dataset
64.0Small, 64.0The name of the date configuration.Stringdate
## Configuration
## Name
64.0Small, 64.0The update operation type. Valid operation
types are:
OperationEnumoperation
## •
## Append
## •
## Delete
## •
## Upsert
## Output D360 Fields Mapping
The fields mapping for an output D360 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The name of the source field.StringsourceField
56.0Small, v56.0The name of the target field.StringtargetField
## Output D360 Node
An output D360 node in a recipe.
## Properties
Inherits properties from Recipe Node.
## 127
Output D360 Fields MappingRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, 56.0The parameters for the node.OutputD360
## Parameters
parameters
## Output D360 Parameters
The parameters for an output D360 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The list of field mappings.OutputD360Fields
## Mapping[]
fieldsMapping
56.0Small, v56.0The name of the D360 object.Stringname
57.0Small, v57.0The streaming parameters.Streaming
## Parameters[]
streaming
56.0Small, v56.0The output type. Valid values are:RecipeD360Output
## Type
type
## •
DateLakeObject
## Output Data Cloud Fields Mapping
The fields mapping for an output Data 360 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, v60.0The data type of the target field. Valid values
are:
RecipeDataTypedataType
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
56.0Small, v56.0The name of the source field.StringsourceField
## 128
Output D360 ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
56.0Small, v56.0The name of the target field.StringtargetField
## Output Data Cloud Node
An output node in a recipe to write to Data 360.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, 60.0The parameters for the node.OutputDataCloud
## Parameters
parameters
## Output Data Cloud Parameters
The parameters for an output Data 360 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, v60.0The data category for the data lake object
## (DLO).
DataObjectCategorycategory
62.0Small, v62.0The connector type. Valid values are:ConnectWaveData
ConnectorTypeEnum
connectorType
## •
AmazonAthena
## •
AmazonRedshiftOutput
## •
AmazonS3
## •
AmazonS3Output
## •
AmazonS3Private
## •
AwsRdsAuroraMySQL
## •
AwsRdsAuroraPostgres
## •
AwsRdsMariaDB
## •
AwsRdsMySQL
## 129
Output Data Cloud NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
## •
AwsRdsPostgres
## •
AwsRdsSqlServer
## •
AzureDataLakeGen2Output
## •
AzureSqlDatabase
## •
AzureSqlDatawarehouse
## •
Databricks(Beta)
## •
GoogleAnalytics4
## •
GoogleBigQuery
## •
GoogleBigQueryDirect
## •
GoogleBigQueryStandardSQL
## •
GoogleSpanner
## •
HerokuPostgres
## •
HubSpot
## •
MarketoV2
## •
NetSuite
## •
OracleEloqua
## •
## Redshift
## •
RedshiftPrivate
## •
SalesforceExternal
## •
SalesforceMarketingCloud
OAuth2
## •
SapHanaCloud
## •
SfdcLocal
## •
SnowflakeComputing
## •
SnowflakeDirect
## •
SnowflakeOutput
## •
SnowflakePrivate
## •
SnowflakePrivateOutput
## •
TableauOnline
## •
TableauHyperOutput
## •
## Zendesk
DEPRECATED: min
60.0, max 64.0
Small, v60.0The dataspace to use in Data 360.AssetReferencedataspace
65.0Small, v65.0A list of dataspaces to use in Data 360.AssetReference[]dataspaces
66.0Small, v66.0The event time field.StringeventTime
## Field
## 130
Output Data Cloud ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
60.0Small, v60.0The list of field mappings.OutputDataCloud
FieldsMapping[]
fieldsMapping
62.0Small, v62.0The label of the Data 360 object.Stringlabel
60.0Small, v60.0The name of the Data 360 object.Stringname
60.0Small, v60.0The name of the primary key field for the
Data 360 object.
StringprimaryKey
60.0Small, v60.0The output type. Valid values are:RecipeDataCloud
OutputTypeEnum
type
## •
DateLakeObject
## Output External Field Mapping
A field mapping for an output external node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The name of the source field.StringsourceField
51.0Small, v51.0The name of the target field.StringtargetField
## Output External Node
An output external node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.OutputExternal
## Parameters
parameters
## 131
Output External Field MappingRecipe REST API Response Bodies

## Output External Parameters
The parameters for an output external node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The connection name.Stringconnection
## Name
51.0Small, v51.0The field name for the external ID.StringexternalId
FieldName
51.0Small, v51.0The list of field mappings.OutputExternalField
## Mapping[]
fieldsMapping
54.0Small, v54.0The name of hyper file.StringhyperFileName
51.0Small, v51.0The object name.Stringobject
51.0Small, v51.0The output external operation type. Valid
values are:
RecipeOutput
ExternalOperation
operation
## •
## Empty
## •
## Insert
## •
## Update
## •
## Upsert
65.0Small, v65.0A map of key/value pairs of a named
credential for a virtual private connection
## (VPC).
Map<String,String>named
## Credential
## Pivot
A pivot for an aggregate data node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The source for the pivot.Stringsource
51.0Small, v51.0The list of values for the pivot.String[]values
## 132
Output External ParametersRecipe REST API Response Bodies

PivotV2
A version 2 pivot for an aggregate data node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The map of the pivot fields information.Map<RecipeName
## Label, List
pivotFields
## Info
54.0Small, v54.0The list of source fields for the pivot.String[]sourceFields
54.0Small, v54.0The list of value combinations for the pivot.String[]value
## Combinations
## Predict Values Field
A field for a predict values node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The label for the field.Stringlabel
51.0Small, v51.0The name for the field.Stringname
51.0Small, v51.0The setup for the predict field.PredictValuesSetup[]prediction
## Setup
## Predict Values Input Field
An input field for a predict values node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The field name.Stringname
## 133
PivotV2Recipe REST API Response Bodies

## Predict Values Node
A predict missing values node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.PredictValues
## Parameters
parameters
## Predict Values Parameters
The parameters for a predict values node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of fields.PredictValuesField[]fields
## Predict Values Setup
The setup for a predict values node field.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of input fields for the model.PredictValuesInput
## Field[]
modelInput
## Fields
51.0Small, v51.0The source field.PredictValuesInput
## Field
sourceField
## Recipe Collection
A collection of data prep recipes.
## 134
Predict Values NodeRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The URL to retrieve the next page of
contents in the collection.
StringnextPageUrl
38.0Small, 38.0A list of recipes.Recipe[]recipes
52.0Medium, 52.0The total count of the elements in the
collection, including all pages.
IntegertotalSize
52.0Small, 52.0The URL to retrieve the collection.Stringurl
## Recipe Configuration Collection
A collection of data prep recipe configurations.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0A list of recipe configurations.Recipe
## Configuration[]
configurations
## Recipe Configuration Fiscal
The data prep recipe fiscal configuration data.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
55.0Small, 55.0The first day of week, calendar and fiscal.IntegerfirstDayOf
## Week
54.0Small, 54.0The recipe configuration fiscal type. Valid
values are:
RecipeConfiguration
TypeEnum
fiscalType
## •
Offset (Recipe Configuration Fiscal
## Offset)
## 135
Recipe Configuration CollectionRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0Indicates whether this recipe configuration
is the default configuration (true) or not
## (false).
BooleanisDefault
## Recipe Configuration Fiscal Offset
The data prep recipe fiscal offset configuration data.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The month offset.StringmonthOffset
54.0Small, 54.0The fiscal offset year based on for the recipe
configuration. Valid values are:
RecipeConfiguration
FiscalOffsetYear
BasedOnEnum
yearBasedOn
## •
## End
## •
## Start
## Recipe Configuration
The data prep recipe configuration data.
## Properties
Recipe Configuration inherits properties from the abstract Base Wave Asset. These base properties appear alongside Recipe Configuration
specific properties in the following table.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The recipe configuration type. Valid values
are:
RecipeConfiguration
TypeEnum
configuration
## Type
## •
Fiscal (Recipe Configuration Fiscal)
## Recipe Conversion Detail
The details for the upconversion of a data prep recipe.
## 136
Recipe Configuration Fiscal OffsetRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The conversion detail ID.Integerconversion
DetailId
52.0Small, 52.0The conversion detail message.Stringmessage
52.0Small, 52.0The name of the node referenced in the
conversion detail.
StringnodeName
52.0Small, 52.0The severity of the conversion detail. Valid
values are:
ConnectRecipe
ConversionSeverity
## Enum
severity
## •
UserInfo
## •
## Warning
## Recipe Definition
The definition for a data prep recipe. Available on for R3 recipes.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The recipe definition name.Stringname
51.0Small, 51.0The map of recipe nodes by name. Valid
values are:
Map<String, Recipe
## Node>
nodes
## •
## Aggregate Node
## •
## Append Node
## •
## Append V2 Node
## •
## Bucket Node
## •
## Bucket V2 Node
## •
## Cluster Node
## •
## Compute Relative Node
## •
## Detect Sentiment Node
## •
## Discovery Node
## •
## Export Node
## •
## Extension Node
## 137
Recipe DefinitionRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
## •
## Extract Node
## •
## Filter Node
## •
## Flatten Node
## •
## Format Date Node
## •
## Formula Node
## •
## Join Node
## •
## Load Node
## •
## Optimized Append Node
## •
## Optimized Update Node
## •
## Output D360 Node
## •
## Output Data Cloud Node
## •
## Output External Node
## •
## Predict Values Node
## •
## Recommendation Node
## •
## Save Node
## •
## Schema Node
## •
## Split Node
## •
SQL Filter Node
## •
## Time Series Node
## •
## Time Series V2 Node
## •
## Typecast Node
## •
## Update Node
57.0Small, v57.0The recipe run mode. Valid values are:RecipeRunModerunMode
## •
## Full
## •
## Incremental
## •
## Streaming
49.0Small, 49.0The recipe definition version.Stringversion
49.0Small, 49.0The recipe definition UI metadata.Objectui
## Recipe Name Label
The name and label for a field in a recipe node.
## 138
Recipe Name LabelRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The label of the field.Stringlabel
51.0Small, v51.0The name of the field.Stringname
## Recipe Node
The base node for a recipe.
As of October 14, 2025, Data Cloud has been rebranded to Data 360. During this transition, you may see references to Data Cloud in our
application and documentation. While the name is new, the functionality and content remains unchanged.
## Properties
Inherited by Aggregate Node, Append Node, Append V2 Node, Bucket Node, Bucket V2 Node, Cluster Node, Compute Relative Node,
Detect Sentiment Node, Discovery Node, Export Node, Extension Node, Extract Node, Filter Node, Flatten Node, Format Date Node,
Formula Node, Join Node, Load Node, Optimized Append Node, Optimized Update Node, Output D360 Node, Output Data Cloud Node,
Output External Node, Predict Values Node, Recommendation Node, Save Node, Schema Node, Split Node, SQL Filter Node, Time Series
Node, Time Series V2 Node, Typecast Node, Update Data Cloud Object Node, and Update Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The recipe node action. Valid recipe actions
are:
RecipeNodeActionaction
## •
## Aggregate
## •
## Append
## •
Append_V2
## •
## Bucket
## •
BucketV2
## •
## Clustering
## •
ComputeRelative
## •
DateFormatConversion
## •
DetectSentiment
## •
DiscoveryPredict
## •
## Export
## •
## Extension
## •
## Extract
## •
## Filter
## •
## Flatten
## 139
Recipe NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
## •
## Formula
## •
## Join
## •
## Load
## •
OptimizedAppendOutput
## •
OptimizedUpdateOutput
## •
OutputD360
## •
OutputExternal
## •
PredictMissingValues
## •
## Recommendation
## •
## Save
## •
## Schema
## •
## Split
## •
SqlFilter
## •
TimeSeries
## •
TimeSeriesV2
## •
TypeCast
## •
## Updatei
## •
UpdateDataCloudObject
## •
WriteDataCloudObject
51.0Small, v51.0The schema changes for the node.SchemaNodeschema
51.0Small, v51.0The input node ids.String[]sources
## Recipe Notification
A notification for a data prep recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The number of minutes that a recipe can
run before sending an alert.
IntegerlongRunning
AlertInMins
49.0Small, 49.0Valid types of email notification levels. Valid
values are:
ConnectEmail
NotificationLevel
## Enum
notification
## Level
## •
## Always
## •
## Failures
## 140
Recipe NotificationRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
## •
## Never
## •
## Warnings
54.0Small, 54.0The recipe this notification belongs to.AssetReferencerecipe
## Recipe Validation Detail
The validation details for a data prep recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
50.0Small, 50.0The message for the validation detail.Stringmessage
50.0Small, 50.0The name of the node referenced in the
validation detail.
StringnodeName
50.0Small, 50.0The type of node referenced in the
validation detail.
StringnodeType
50.0Small, 50.0The severity of the validation detail. Valid
values are:
ConnectRecipe
ValidationSeverity
## Enum
severity
## •
Error - The recipe is non-runnable
and can’t be saved.
## •
Fatal - The validation process is
stopped. The recipe is non-runnable
and can’t be saved.
## •
Warning - The recipe is non-runnable,
but can be saved.
50.0Small, 50.0The validation action.Stringvalidation
## Action
50.0Small, 50.0The validation code.Integervalidation
## Code
## Recipe
A data prep recipe.
## 141
Recipe Validation DetailRecipe REST API Response Bodies

## Properties
Recipe inherits properties from the abstract Base Wave Asset. These base properties appear alongside Recipe specific properties in the
following table.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The list of upconversion details when
converting the recipe to R3.
RecipeConversion
## Detail[]
conversion
## Details
38.0Small, 38.0The date of the last recipe dataflow update.DatedataflowLast
## Update
38.0Small, 38.0The target dataset.AssetReferencedataset
38.0Small, 38.0The URL to get the recipe's JSON file content
(see /wave/recipes/<recipeId>/file for more
information).
StringfileUrl
48.0Small, 48.0Specifies the format of the returned recipe.
Valid values are:
ConnectRecipe
FormatTypeEnum
format
## •
R2 (Data Prep Classic)
## •
R3 (Data Prep)
51.0Small, 51.0The URL for the version histories associated
with the recipe.
StringhistoriesUrl
52.0Small, 52.0The Analytics license type. Valid values areConnectAnalytics
LicenseTypeEnum
licenseType
## •
Cdp (Data 360)
## •
DataPipelineQuery (Data
## Pipeline Query)
## •
EinsteinAnalytics (CRM
## Analytics)
## •
IntelligentApps (Intelligent
## Apps)
## •
MulesoftDataPath (Mulesoft
## Data Works)
## •
Sonic (Salesforce Data Pipeline)
47.0Small, 47.0The next scheduled run of this recipe.DatenextScheduled
## Date
42.0Small, 42.0The target format or system to publish the
recipe to. Valid values are:
ConnectRecipe
PublishingTarget
## Enum
publishing
## Target
## •
Dataset (Publish to Dataset)
49.0Small, 49.0The recipe definition for the Data Prep
recipe only. This property isn’t supported
for Data Prep Classic recipes.
RecipeDefinitionrecipe
## Definition
## 142
RecipeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
38.0Small, 38.0The security predicate of the target dataset.StringrowLevel
## Security
## Predicate
38.0Small, 38.0The schedule cron expression for the current
dataflow.
## Stringschedule
53.0Small, 53.0The schedule for the recipe.Scheduleschedule
## Attributes
49.0Small, 49.0The schedule type of the recipe. Valid values
are:
ConnectRecipe
ScheduleTypeEnum
scheduleType
## •
EventDriven
## •
TimeDriven
51.0Small, v51.0The dataflow used to upconvert or revert
the current recipe.
## Stringsource
## Dataflow
50.0Small, 50.0The recipe used to upconvert or revert the
current recipe.
StringsourceRecipe
54.0Small, 54.0The status of the recipe. Valid values are:ConnectRecipeStatus
## Enum
status
## •
## Cancelled
## •
## Failure
## •
New (Never run or has no recent run)
## •
## Queued
## •
## Running
## •
## Success
## •
## Warning
42.0Small, 42.0The target dataflow ID.Stringtarget
DataflowId
50.0Small, 50.0The collection of validation details for a Data
Prep recipe. This property isn’t supported
for Data Prep Classic recipes.
RecipeValidation
## Detail[]
validation
## Details
## Recommendation Node
A recommendation node in a recipe.
## Properties
Inherits properties from Recipe Node.
## 143
Recommendation NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The parameters for the node.Recommendation
## Parameters
parameters
## Recommendation Parameters
The parameters for a recommendation node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, v53.0The customer ID field.StringcustIdField
53.0Small, v53.0Indicates whether to exclude previous
recommendations (true) or not (false).
## Booleanexclude
## Previous
## Recommendations
53.0Small, v53.0The product ID field.StringproductId
## Field
53.0Small, v53.0The product recommendations field.Integerproduct
## Recommendations
53.0Small, v53.0The rating field.StringratingField
53.0Small, v53.0The target field.RecipeNameLabeltargetField
53.0Small, v53.0The target rank field.RecipeNameLabeltargetRank
## Field
53.0Small, v53.0The target rating field.RecipeNameLabeltargetRating
## Field
53.0Small, v53.0Indicates whether to use implicit ratings
(true) or not (false).
BooleanuseImplicit
## Ratings
## Sample Parameters
The sample parameters for loading data.
## 144
Recommendation ParametersRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
55.0Small, v55.0The sample filters.FilterParametersfilters
55.0Small, v55.0A list of fields to sort sample.String[]sortBy
55.0Small, v55.0The sample sort direction. Valid values are:RecipeSortOrder
## Enum
sortDirection
## •
## Ascending
## •
## Descending
55.0Small, v55.0The recipe sample type. Valid values are:SampleTypesampleType
## •
## Custom
## •
## Random
## •
TopN
## •
## Unique
55.0Small, v55.0The field name for a unique sample.StringuniqueSample
FieldName
## Save Dataset
The dataset for a save node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The analytics folder for the dataset.StringfolderName
53.0Small, v53.0Indicates whether the data is staged (true)
or not (false).
BooleanisStaged
51.0Small, v51.0The label for the dataset.Stringlabel
51.0Small, v51.0The name of the dataset.Stringname
51.0Small, v51.0The security predicate.StringrowLevel
## Security
## Filter
51.0Small, v51.0The sObject security sharing source.StringrowLevel
SharingSource
51.0Small, v51.0The type of the dataset.Stringtype
## 145
Save DatasetRecipe REST API Response Bodies

## Save Node
A save data node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.SaveParametersparameters
## Save Parameters
The parameters for a save node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The dataset to save.SaveDatasetdataset
55.0Small, v55.0The date configuration name.Stringdate
## Configuration
## Name
51.0Small, v51.0The list of fields to save.String[]fields
56.0Small, v56.0A list of the measures to currencies.MeasureTo
## Currency[]
measuresTo
## Currencies
## Schema Field Format Symbols
The field format symbols for a schema node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The currency symbol format.Stringcurrency
## Symbol
51.0Small, v51.0The decimal symbol format.StringdecimalSymbol
## 146
Save NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The grouping symbol format.Stringgrouping
## Symbol
## Schema Field
The field for a schema node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0The value to output on error.StringerrorValue
49.0Small, v49.0The schema field name.Stringname
49.0Small, v49.0The new schema field properties.SchemaFieldNew
## Properties
newProperties
## Schema Field New Properties
The new field properties for a schema node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, v49.0The schema field property label.Stringlabel
49.0Small, v49.0The schema field property name.Stringname
49.0Small, v49.0The new schema field type properties.SchemaFieldType
## Properties
type
## Properties
## Schema Field Type Properties
The field type properties for a schema node in a recipe.
## 147
Schema FieldRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The DateTime format.Stringformat
51.0Small, v51.0The total length of the text.Integerlength
51.0OptionalThe length of an arbitrary precision value.Integerprecision
51.0Small, v51.0The number of digits to the right of the
decimal point.
## Integerscale
51.0Small, v51.0The number format.SchemaFieldFormat
## Symbols
symbols
51.0Small, v51.0The recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Schema Node
A schema node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The schema fields for the node.SchemaParameters[]fields
## Schema Parameters
The parameters for a schema node in a recipe.
## 148
Schema NodeRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The schema fields for the node.SchemaField[]fields
51.0Small, v51.0The schema slice definition for the node.SchemaSliceslice
## Schema Slice
The slice definition for a schema node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of fields for SELECT or DROP.String[]fields
51.0Small, v51.0Indicates whether the node action ignores
missing fields (true) or not (false).
BooleanignoreMissing
## Fields
51.0Small, v51.0The slice mode. Valid values are:Stringmode
## •
## SELECT
## •
## DROP
## Split Node
A split node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
49.0Small, 49.0The parameters for the node.SplitParametersparameters
## Split Parameters
The parameters for a split node in a recipe.
## 149
Schema SliceRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The split delimiter.Stringdelimiter
51.0Small, v51.0The source field.StringsourceField
51.0Small, v51.0The list of target fields.RecipeNameLabel[]targetFields
SQL Filter Node
A SQL filter node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, 53.0The parameters for the node.SQLFilterParametersparameters
SQL Filter Parameters
The parameters for a SQL filter node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
53.0Small, v53.0The SQL filter expression.StringsqlFilter
## Expression
SQL Formula Date Field
The SQL formula date field for a recipe node.
## Properties
Inherits properties from SQL Formula Field.
## 150
SQL Filter NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The format for the date field.Stringformat
SQL Formula Field
The base SQL formula field for a recipe node.
## Properties
Inherited by SQL Formula Date Field, SQL Formula Multivalue Field, SQL Formula Numeric Field, and SQL Formula Text Field.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The default value for the field.StringdefaultValue
51.0Small, v51.0The formula expression.Stringformula
## Expression
51.0Small, v51.0The formula label.Stringlabel
51.0Small, v51.0The formula name.Stringname
51.0Small, v51.0The recipe data type. Valid values are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
SQL Formula Parameters
The SQL formula parameters for a formula.
## Properties
Inherits properties from Formula Parameters.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0RequiredThe list of fields.SQLFormulaField[]fields
## 151
SQL Formula FieldRecipe REST API Response Bodies

SQL Formula Multivalue Field
The SQL formula multivalue field for a recipe node.
## Properties
Inherits properties from SQL Formula Field.
SQL Formula Numeric Field
The SQL formula numeric field for a recipe node.
## Properties
Inherits properties from SQL Formula Field.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The precision for the numeric field.Integerprecision
51.0Small, v51.0The scale for the numeric field.Integerscale
SQL Formula Text Field
The SQL formula text field for a recipe node.
## Properties
Inherits properties from SQL Formula Field.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The precision for the text field.Integerprecision
## Streaming Parameters
The streaming parameters for data output.
## 152
SQL Formula Multivalue FieldRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
57.0Small, 57.0The output mode. Valid values are:OutputModeEnumoutputMode
## •
## Append
## •
## Complete
## •
## Update
57.0Small, 57.0The trigger interval in seconds.Integertrigger
IntervalSec
57.0Small, 57.0The trigger type. Valid values are:TriggerTypeEnumtriggerType
## •
## Fixed
## Target Field
A target field for a recipe bucket.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
64.0Small, 64.0The label for the field.Stringlabel
64.0Small, 64.0The name for the field.Stringname
64.0Small, 64.0The data type. Valid recipe data types are:RecipeDataTypetype
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
## Time Series Node
A time series node in a recipe.
## Properties
Inherits properties from Recipe Node.
## 153
Target FieldRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, 52.0The parameters for the node.TimeSeries
## Parameters
parameters
## Time Series Output Confidence Interval High Low
A confidence interval for a time series recipe node.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0The high confidence interval.RecipeNameLabelhigh
52.0Small, v52.0The low confidence interval.RecipeNameLabellow
## Time Series Parameters
The parameters for a time series node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The confidence interval. Valid values are:RecipeTimeSeries
ConfidenceInterval
## Type
confidence
## Interval
## •
## Eighty
## •
NinetyFive
## •
## None
52.0Small, v52.0The confidence interval field name and
labels.
Map<String, Time
SeriesOutput
ConfidenceInterval
HighLow>
confidence
## Interval
## Fields
51.0Small, v51.0The day field.StringdayField
51.0Small, v51.0The list of forecast fields.String[]forecast
## Fields
51.0Small, v51.0The forecast length.Integerforecast
## Length
## 154
Time Series Output Confidence Interval High LowRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The value to group dates by. Valid values
are:
RecipeGroupDatesBygroupDatesBy
## •
## Year
## •
YearMonth
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
51.0Small, v51.0Indicates whether to ignore the last time
period (true) or not (false).
BooleanignoreLast
TimePeriod
51.0Small, v51.0The time series model. Valid values are:RecipeTimeSeries
## Model
model
## •
## Additive
## •
## Auto
## •
## Multiplicative
51.0Small, v51.0The seasonality.Integerseasonality
51.0Small, v51.0The sub year field.StringsubYearField
51.0Small, v51.0The target date field.RecipeNameLabeltargetDate
## Field
51.0Small, v51.0The list of target forecast fields.RecipeNameLabel[]target
## Forecast
## Fields
51.0Small, v51.0The year field.StringyearField
## Time Series V2 Algorithm Parameters
The algorithm parameters for a time series version 2 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The time series model. Valid values are:RecipeTimeSeries
## Model
model
## •
## Additive
## •
## Auto
## •
## Multiplicative
## 155
Time Series V2 Algorithm ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The seasonality value.Integerseasonality
## Time Series V2 Forecast Info
The forecast information for a time series version 2 node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The aggregate data.Aggregateaggregate
54.0Small, v54.0The confidence interval field name and
labels.
TimeSeriesOutput
ConfidenceInterval
HighLow
confidence
## Interval
## Fields
54.0Small, v54.0The aggregate data.RecipeNameLabelforecastField
## Time Series V2 Node
A time series version 2 node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, 54.0The parameters for the node.TimeSeriesV2
## Parameters
parameters
## Time Series V2 Parameters
The parameters for a time series version 2 node in a recipe.
## 156
Time Series V2 Forecast InfoRecipe REST API Response Bodies

## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The forecast algorithm. Valid values are:TimeSeriesV2
ForecastAlgorithm
## Enum
algorithm
## •
HoltWinters
54.0Small, v54.0The parameters for the algorithm.TimeSeriesV2
## Algorithm
## Parameters
algorithm
## Parameters
54.0Small, v54.0The confidence interval. Valid values are:RecipeTimeSeries
ConfidenceInterval
## Type
confidence
## Interval
## •
## Eighty
## •
NinetyFive
## •
## None
54.0Small, v54.0The forecast date field.StringforecastDate
## Field
54.0Small, v54.0The value to group dates by. Valid values
are:
RecipeGroupDatesByforecastDates
## By
## •
FiscalYear
## •
FiscalYearMonth
## •
FiscalYearQuarter
## •
FiscalYearWeek
## •
YearMonth
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
54.0Small, v54.0The list of forecast fields.TimeSeriesV2
ForecastInfo[]
forecast
## Fields
54.0Small, v54.0The forecast length.Integerforecast
## Length
54.0Small, v54.0The forecast length type. Valid values are:TimeSeriesV2
ForecastLengthType
## Enum
forecast
LengthType
## •
## Rolling
54.0Small, v54.0The list of partition groupings.ExtractParameter[]grouping
## Fields
54.0Small, v54.0The partial data handling value. Valid values
are:
TimeSeriesV2Partial
DataHandlingEnum
partialData
## Handling
## •
IgnoreLast
## •
## None
## 157
Time Series V2 ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The target date field.RecipeNameLabeltargetDate
## Field
## Typecast Node
A typecast node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, 51.0The parameters for the node.TypecastParametersparameters
## Typecast Parameters
The parameters for a typecast node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The list of fields to typecast.SchemaField[]fields
## Typographic Cluster
The configuration for a typographic cluster algorithm.
## Properties
Inherits properties from AbstractBucketAlgorithm.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0The edit distanceIntegerdistance
## Threshold
## 158
Typecast NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
52.0Small, v52.0Indicates whether to ignore case (true) or
not (false).
BooleanignoreCase
## Update Data Cloud Object Node
A Data 360 object update node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Small, v66.0The parameters for the node.UpdateDataCloud
ObjectParameters
parameters
## Update Data Cloud Object Parameters
The parameters for an update data cloud object node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Small, v66.0The connector type. Valid values are:ConnectWaveData
ConnectorTypeEnum
connectorType
## •
AmazonAthena
## •
AmazonRedshiftOutput
## •
AmazonS3
## •
AmazonS3Output
## •
AmazonS3Private
## •
AwsRdsAuroraMySQL
## •
AwsRdsAuroraPostgres
## •
AwsRdsMariaDB
## •
AwsRdsMySQL
## •
AwsRdsPostgres
## •
AwsRdsSqlServer
## •
AzureDataLakeGen2Output
## 159
Update Data Cloud Object NodeRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
## •
AzureSqlDatabase
## •
AzureSqlDatawarehouse
## •
Databricks(Beta)
## •
GoogleAnalytics4
## •
GoogleBigQuery
## •
GoogleBigQueryDirect
## •
GoogleBigQueryStandardSQL
## •
GoogleSpanner
## •
HerokuPostgres
## •
HubSpot
## •
MarketoV2
## •
NetSuite
## •
OracleEloqua
## •
## Redshift
## •
RedshiftPrivate
## •
SalesforceExternal
## •
SalesforceMarketingCloud
OAuth2
## •
SapHanaCloud
## •
SfdcLocal
## •
SnowflakeComputing
## •
SnowflakeDirect
## •
SnowflakeOutput
## •
SnowflakePrivate
## •
SnowflakePrivateOutput
## •
TableauOnline
## •
TableauHyperOutput
## •
## Zendesk
66.0Small, v66.0The list of the Data 360 field mappings.List[ OutputData
CloudFields
## Mapping]
fieldMappings
66.0Small, v66.0The name of the Data 360 object to update.Stringname
66.0Small, v66.0The update operation. Valid values are:OperationEnumoperation
## •
## Append
## •
## Delete
## •
## Upsert
## 160
Update Data Cloud Object ParametersRecipe REST API Response Bodies

Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
66.0Small, v66.0The name of the primary key field.StringprimaryKey
66.0Small, v66.0The output type. Valid values are:RecipeDataCloud
OutputTypeEnum
type
## •
DateLakeObject
## Update Node
An update node in a recipe.
## Properties
Inherits properties from Recipe Node.
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
51.0Small, v51.0The parameters for the node.UpdateParametersparameters
## Update Parameters
The parameters for an update node in a recipe.
## Properties
Available VersionFilter Group and
## Version
DescriptionTypeProperty Name
54.0Small, v54.0The list of left keys.String[]leftKeys
54.0Small, v54.0The right of left keys.String[]rightKeys
54.0Small, v54.0The map of columns to update.Map<String, String>updateColumns
## 161
Update NodeRecipe REST API Response Bodies

## RECIPE REST API APPENDICES
Use these appendices when working with enums and other shared resources.
Recipe REST API Enums
Enums specific to the /wave/recipes namespace
Recipe REST API Enums
Enums specific to the /wave/recipes namespace
Enums are not versioned. Enum Values are returned in all API versions. Clients should handle values they don't understand gracefully.
DescriptionEnum
The Analytics license types. Valid values are:ConnectAnalyticsLicenseTypeEnum
## •
Cdp (Data 360)
## •
DataPipelineQuery (Data Pipeline Query)
## •
EinsteinAnalytics (CRM Analytics)
## •
IntelligentApps (Intelligent Apps)
## •
MulesoftDataPath (Mulesoft Data Works)
## •
Sonic (Salesforce Data Pipeline)
Valid types of email notification levels you can set. Valid values are:ConnectEmailNotificationLevelEnum
## •
## Always
## •
## Failures
## •
## Never
## •
## Warnings
The severity of the conversion detail. Valid values are:ConnectRecipeConversionSeverity
## Enum
## •
UserInfo
## •
## Warning
The recipe's execution engine. Valid values are:ConnectRecipeExecutionEngine
## Enum
## •
## V1
## •
## V2
Returns a collection filtered by the format of the current recipe definition. Valid values are:ConnectRecipeFormatTypeEnum
## •
R2 (Data Prep Classic)
## •
R3 (Data Prep)
## 162

DescriptionEnum
The target format or system to publish the recipe to. Valid values are:ConnectRecipePublishingTarget
## Enum
## •
Dataset (Publish to Dataset)
The schedule type of the recipe. Valid values are:ConnectRecipeScheduleTypeEnum
## •
EventDriven
## •
TimeDriven
The status of the recipe. Valid values are:ConnectRecipeStatusEnum
## •
## Cancelled
## •
## Failure
## •
New (Never run or has no recent run)
## •
## Queued
## •
## Running
## •
## Success
## •
## Warning
The recipe validation context. Valid values are:ConnectRecipeValidationContext
## Enum
## •
## Default
## •
## Editor
The type of Analytics connector. The valid values are:ConnectWaveDataConnectorType
## Enum
## •
AmazonAthena
## •
AmazonRedshiftOutput
## •
AmazonS3
## •
AmazonS3Output
## •
AmazonS3Private
## •
AwsRdsAuroraMySQL
## •
AwsRdsAuroraPostgres
## •
AwsRdsMariaDB
## •
AwsRdsMySQL
## •
AwsRdsPostgres
## •
AwsRdsSqlServer
## •
AzureDataLakeGen2Output
## •
AzureSqlDatabase
## •
AzureSqlDatawarehouse
## •
Databricks(Beta)
## •
GoogleAnalytics4
## •
GoogleBigQuery
## •
GoogleBigQueryDirect
## 163
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
## •
GoogleBigQueryStandardSQL
## •
GoogleSpanner
## •
HerokuPostgres
## •
HubSpot
## •
MarketoV2
## •
NetSuite
## •
OracleEloqua
## •
## Redshift
## •
RedshiftPrivate
## •
SalesforceExternal
## •
SalesforceMarketingCloudOAuth2
## •
SapHanaCloud
## •
SfdcLocal
## •
SnowflakeComputing
## •
SnowflakeDirect
## •
SnowflakeOutput
## •
SnowflakePrivate
## •
SnowflakePrivateOutput
## •
TableauOnline
## •
TableauHyperOutput
## •
## Zendesk
The mode for accessing connected datasets. Valid values are:ConnectionModeEnum
## •
## AUTO
## •
## DIRECT
## •
## SYNCED
The output type. Valid values are:DetectSentimentOutputTypeEnum
## •
## Dimension
## •
## Measure
The input run mode. Valid values are:InputRunModeEnum
## •
## Full
## •
## Incremental
## •
## Streaming
The scaling type. Valid values are:MeasureScalingTypeEnum
## •
MinMaxScaling
## 164
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
The operation type for append. Valid values are:OperationEnum
## •
## Append
## •
## Delete
## •
## Upsert
The output mode. Valid values are:OutputModeEnum
## •
## Append
## •
## Complete
## •
## Update
The aggregate type for the node. Valid values are:RecipeAggregateNodeEnum
## •
## Hierarchical
## •
## Standard
The recipe aggregation type. Valid values are:RecipeAggregateType
## •
## Avg
## •
## Count
## •
## Maximum
## •
## Median
## •
## Minimum
## •
StdDev
## •
StdDevP
## •
## Sum
## •
## Unique
## •
## Var
## •
VarP
The recipe bucket field algorithm type. Valid values are:RecipeBucketAlgorithmType
## •
TypographicClustering
The recipe bucket date grain type. Valid values are:RecipeBucketGrain
## •
AbsoluteDate
## •
## Days
## •
FiscalQuarters
## •
FiscalYears
## •
## Months
## •
## Quarters
## •
## Weeks
## •
## Years
## 165
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
The recipe configuration fiscal offset year based on type. Valid values are:RecipeConfigurationFiscalOffsetYear
BasedOnEnum
## •
## End
## •
## Start
The recipe configuration fiscal type. Valid values are:RecipeConfigurationFiscalTypeEnum
## •
## Offset
The output type. Valid values are:RecipeD360OutputType
## •
DateLakeObject
The output type. Valid values are:RecipeDataCloudOutputTypeEnum
## •
DateLakeObject
The recipe data type. Valid values are:RecipeDataType
## •
DateOnly
## •
DateTime
## •
## Multivalue
## •
## Number
## •
## Text
The extract grain type. Valid values are:RecipeDateGrain
## •
## Day
## •
DayEpoch
## •
FiscalMonth
## •
FiscalQuarter
## •
FiscalWeek
## •
FiscalYear
## •
## Hour
## •
## Minute
## •
## Month
## •
## Quarter
## •
## Second
## •
SecondEpoch
## •
## Week
## •
## Year
The type of the dataset. Valid values are:RecipeDatasetType
## •
## Analytics
## •
## Connected
## •
DataLakeObject
## 166
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
## •
DataModelObject
The type of the recipe export CSV header row value. Valid values are:RecipeExportCsvHeaderRowValue
## Type
## •
FullyQualifiedName
## •
## Label
The format of the export. Valid values are:RecipeExportFormat
## •
## CSV.
The formula expression type. Valid values are:RecipeFormulaExpressionType
## •
## Legacy
## •
## Sql
The value to group dates by. Valid values are:RecipeGroupDatesBy
## •
## Year
## •
YearMonth
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
The value to group dates by. Valid values are:RecipeGroupDatesByV2
## •
FiscalYear
## •
FiscalYearMonth
## •
FiscalYearQuarter
## •
FiscalYearWeek
## •
YearMonth
## •
YearMonthDay
## •
YearQuarter
## •
YearWeek
The join type. Valid values are:RecipeJoinType
## •
## Cross
## •
## Inner
## •
LeftOuter
## •
## Lookup
## •
MultiValueLookup
## •
## Outer
## •
RightOuter
The recipe node action. Valid recipe actions are:RecipeNodeAction
## •
## Aggregate
## 167
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
## •
## Append
## •
Append_V2
## •
## Bucket
## •
BucketV2
## •
## Clustering
## •
ComputeRelative
## •
DateFormatConversion
## •
DetectSentiment
## •
DiscoveryPredict
## •
## Export
## •
## Extension
## •
## Extract
## •
## Filter
## •
## Flatten
## •
## Formula
## •
## Join
## •
## Load
## •
OptimizedAppendOutput
## •
OptimizedUpdateOutput
## •
OutputD360
## •
OutputExternal
## •
PredictMissingValues
## •
## Recommendation
## •
## Save
## •
## Schema
## •
## Split
## •
SqlFilter
## •
TimeSeries
## •
TimeSeriesV2
## •
TypeCast
## •
## Updatei
## •
UpdateDataCloudObject
## •
WriteDataCloudObject
The output external operation type. Valid values are:RecipeOutputExternalOperation
## •
## Empty
## •
## Insert
## •
## Update
## 168
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
## •
## Upsert
The recipe run mode. Valid values are:RecipeRunMode
## •
## Full
## •
## Incremental
## •
## Streaming
The slice mode. Valid values are:RecipeSliceMode
## •
## SELECT
## •
## DROP
The recipe sort order. Valid values are:RecipeSortOrderEnum
## •
## Ascending
## •
## Descending
The confidence interval. Valid values are:RecipeTimeSeriesConfidenceInterval
## Type
## •
## Eighty
## •
NinetyFive
## •
## None
The time series model. Valid values are:RecipeTimeSeriesModel
## •
## Additive
## •
## Auto
## •
## Multiplicative
The recipe sample type. Valid values are:SampleType
## •
## Custom
## •
## Random
## •
TopN
## •
## Unique
The sentiment score type. Valid values are:SentimentScoreTypeEnum
## •
## All
## •
## None
The forecast algorithm. Valid values are:TimeSeriesV2ForecastAlgorithm
## Enum
## •
HoltWinters
The forecast length type. Valid values are:TimeSeriesV2ForecastLengthType
## Enum
## •
## Rolling
## 169
Recipe REST API EnumsRecipe REST API Appendices

DescriptionEnum
The partial data handling value. Valid values are:TimeSeriesV2PartialDataHandling
## Enum
## •
IgnoreLast
## •
## None
The trigger type. Valid values are:TriggerTypeEnum
## •
## Fixed
Available VersionRequired or
## Optional
DescriptionEnumProperty Name
38.0OptionalThe type of sort order to be applied to the
returned collection. Valid values are:
ConnectWaveSort
OrderTypeEnum
sort
## •
## App
## •
CreatedBy
## •
CreatedById
## •
CreatedDate
## •
FolderName
## •
LastModified
## •
LastModifiedBy
## •
LastModifiedById
## •
LastModifiedDate
## •
## Location
## •
Mru (Most Recently Used, last viewed
date)
## •
## Name
## •
## Outcome
## •
RefreshDate (for assets like
datasets)
## •
RunDate (for assets like reports)
## •
## Status
## •
## Title
## •
## Type
## 170
Recipe REST API EnumsRecipe REST API Appendices