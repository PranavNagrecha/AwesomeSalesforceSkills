#!/usr/bin/env python3
"""Checker for Collaborative Forecasts metadata and quota load files.

Stdlib only. Every rule below is grounded in the Metadata API Developer Guide
(ForecastingSettings, ForecastingType, ForecastingSourceDefinition,
ForecastingTypeSource, ForecastingFilter/Condition, CustomValue) or the Object
Reference (ForecastingQuota, ForecastingType, User, UserRole).

Usage:
    python3 check_collaborative_forecasts.py --manifest-dir force-app/main/default
    python3 check_collaborative_forecasts.py --manifest-dir . --quiet

Checks performed:
  1. Forecasting.settings parses, is named correctly, and carries all eight
     forecastingCategoryMappings occurrences.
  2. Every active forecastingTypeSettings block uses one coherent set of four
     displayed/forecasted category API names, drawn from the documented enums,
     with displayed == forecasted.
  3. Enum validity for forecastingDateType, periodType, forecastingCategoryMappings
     rollup names, weightedSourceCategories source names, and adjustable category
     names; forecast type `name` against the guide's fixed list.
  4. Measure coherence: isAmount/isQuantity (and amount/quantity on
     ForecastingType) must be exact opposites; a quantity type must not be
     declared isAmount true.
  5. ForecastingType / ForecastingSourceDefinition / ForecastingTypeSource
     enum and cross-reference sanity (roleType, sourceObject, measureField,
     dateField, relationField, adjustable-category pairing).
  6. Opportunity stage forecastCategory values in StandardValueSet:OpportunityStage.
  7. ForecastingQuota CSV lint: required columns, read-only columns, and
     amount/quantity exclusivity.
  8. User CSV lint: ForecastEnabled true with no role assignment.

Exit code 0 when nothing is flagged, 1 otherwise.
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Grounded constants
# ---------------------------------------------------------------------------

MAX_ACTIVE_FORECAST_TYPES = 4  # api_meta 117503: "maximum number of forecast types is four"

# api_meta 117615 / 117640: displayedCategoryApiNames / forecastedCategoryApiNames
CUMULATIVE_SET = {"openpipeline", "bestcaseforecast", "commitforecast", "closedonly"}
INDIVIDUAL_SET = {"pipelineonly", "bestcaseonly", "commitonly", "closedonly"}
# forecastedCategoryApiNames additionally allows customcategory in both styles
EXTRA_FORECASTED = {"customcategory"}

# api_meta 117534 ff: forecastingItemCategoryApiName valid values (eight required)
ROLLUP_CATEGORY_NAMES = {
    "openpipeline", "bestcaseforecast", "commitforecast",
    "pipelineonly", "bestcaseonly", "commitonly",
    "closedonly", "omittedonly", "customcategory",
}
REQUIRED_MAPPING_COUNT = 8  # api_meta 117520 and 117530

# api_meta 117969 ff: WeightedSourceCategory.sourceCategoryApiName
SOURCE_CATEGORY_NAMES = {"pipeline", "best case", "commit", "closed", "omitted", "customcategory", "most likely"}

# api_meta 117703 / 117799: adjustable categories, two values, Best Case + Commit only
CUMULATIVE_ADJUSTABLE = {"bestcaseforecast", "commitforecast"}
INDIVIDUAL_ADJUSTABLE = {"bestcaseonly", "commitonly"}

# api_meta 117659 ff: ForecastingDateType enumeration
DATE_TYPES = {
    "OpportunityCloseDate", "ProductDate", "ScheduleDate",
    "OLIMeasureCloseDateOnly", "ProductDateOnly", "ScheduleDateOnly",
    "OpportunityCustomDate", "OLIMeasureOppCustomDateOnly",
}

# api_meta 117913 ff: PeriodTypes enumeration on ForecastRangeSettings
PERIOD_TYPES = {"Month", "Quarter", "Week", "Year"}
MAX_DISPLAYING_MONTHS = 12  # api_meta 117910
MAX_DISPLAYING_QUARTERS = 8

# api_meta 117722 ff: forecast type names activatable through ForecastingSettings
LEGACY_TYPE_NAMES = {
    "LineItemQuantityProductDate", "LineItemQuantityScheduleDate",
    "LineItemRevenueProductDate", "LineItemRevenueScheduleDate",
    "OpportunityLineItemQuantity", "OpportunityLineItemRevenue",
    "OpportunityOverlayRevenue", "OpportunityQuantity",
    "OpportunityQuantityProductDate", "OpportunityQuantityScheduleDate",
    "OpportunityRevenue", "OpportunityRevenueProductDate",
    "OpportunityRevenueScheduleDate", "OpportunitySplitRevenue",
}

# api_meta 75264 ff: ForecastingType.roleType
ROLE_TYPES = {"R", "Y"}

# api_meta 75066 ff: ForecastingSourceDefinition enums
SOURCE_OBJECTS = {"Opportunity", "OpportunityLineItem", "OpportunityLineItemSchedule", "OpportunitySplit", "Product2"}
DATE_FIELDS = {"Opportunity.CloseDate", "OpportunityLineItem.ServiceDate", "OpportunityLineItemSchedule.ScheduleDate"}
MEASURE_FIELD_PREFIXES = ("Opportunity.", "OpportunityLineItem.", "OpportunityLineItemSchedule.", "OpportunitySplit.")
USER_FIELDS = {"Opportunity.OwnerId", "OpportunitySplit.SplitOwnerId"}
CATEGORY_FIELDS = {"Opportunity.ForecastCategoryName"}
TERRITORY2_FIELDS = {"Opportunity.Territory2Id"}
QUANTITY_MEASURES = {
    "Opportunity.TotalOpportunityQuantity",
    "OpportunityLineItem.Quantity",
    "OpportunityLineItemSchedule.Quantity",
}

# api_meta 75413 ff: ForecastingTypeSource.relationField
RELATION_FIELDS = {
    "OpportunityLineItem.OpportunityId", "OpportunityLineItem.Product2Id",
    "OpportunityLineItemSchedule.OpportunityLineItemId", "OpportunitySplit.OpportunityId",
}

# api_meta 74972 ff: FilterOperation
FILTER_OPERATIONS = {"equals", "greaterOrEqual", "greaterThan", "lessOrEqual", "lessThan", "notEqual"}
MAX_FILTER_CONDITIONS = 3  # api_meta 75041

# api_meta 47578: CustomValue.forecastCategory (ForecastCategories enumeration)
STAGE_FORECAST_CATEGORIES = {"Omitted", "Pipeline", "BestCase", "Forecast", "Closed"}
# Values practitioners reach for that the metadata enum does not accept
STAGE_CATEGORY_ALIASES = {
    "Commit": "Forecast",
    "Best Case": "BestCase",
    "MostLikely": None,
    "Most Likely": None,
}

# object_reference 147887 ff: ForecastingQuota
QUOTA_REQUIRED = {"quotaownerid", "startdate"}
QUOTA_READ_ONLY = {
    "periodid": "PeriodId is read only (object_reference 147978)",
    "isamount": "IsAmount has no Create property; it is derived from the forecast type (object_reference 147946)",
    "isquantity": "IsQuantity has no Create property; it is derived from the forecast type (object_reference 147955)",
}
QUOTA_MEASURES = {"quotaamount", "quotaquantity"}


# ---------------------------------------------------------------------------
# XML helpers
#
# NOTE: never write `el.find(a) or el.find(b)` on ElementTree elements -- an
# Element with no children is falsy even when it exists. Everything below tests
# `is not None` explicitly, or iterates children by stripped tag name.
# ---------------------------------------------------------------------------

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def child_texts(element, tag: str) -> list[str]:
    """All direct children with this tag, as stripped text (order preserved)."""
    return [(c.text or "").strip() for c in element if strip_ns(c.tag) == tag]


def child_text(element, tag: str, default: str = "") -> str:
    """Text of the first direct child with this tag; default when absent."""
    for c in element:
        if strip_ns(c.tag) == tag:
            return (c.text or "").strip()
    return default


def has_child(element, tag: str) -> bool:
    for c in element:
        if strip_ns(c.tag) == tag:
            return True
    return False


def child_elements(element, tag: str) -> list:
    return [c for c in element if strip_ns(c.tag) == tag]


def parse_xml(path: Path):
    """Return (root, error_message). Exactly one of the two is None."""
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"{path}: not well-formed XML -- {exc}"
    except OSError as exc:
        return None, f"{path}: unreadable -- {exc}"


def files_named(root: Path, *patterns: str) -> list[Path]:
    out: list[Path] = []
    for pattern in patterns:
        out.extend(sorted(root.rglob(pattern)))
    return out


def root_tag_is(root, name: str) -> bool:
    return root is not None and strip_ns(root.tag) == name


# ---------------------------------------------------------------------------
# Check 1-4: ForecastingSettings
# ---------------------------------------------------------------------------

def check_forecasting_settings(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    misnamed = files_named(manifest_dir, "ForecastingSettings.settings", "ForecastingSettings.settings-meta.xml")
    for path in misnamed:
        issues.append(
            f"{path}: wrong file name. ForecastingSettings values are stored in a single file named "
            "'Forecasting.settings' in the settings directory (api_meta 117448). A file called "
            "ForecastingSettings.settings will not be recognised on deploy."
        )

    settings_files = files_named(manifest_dir, "Forecasting.settings", "Forecasting.settings-meta.xml")
    if not settings_files and not misnamed:
        return issues  # nothing to check; check_nothing_found reports the empty case

    for path in settings_files:
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        if not root_tag_is(root, "ForecastingSettings"):
            issues.append(f"{path}: root element is <{strip_ns(root.tag)}>, expected <ForecastingSettings>.")
            continue

        issues.extend(_check_category_mappings(path, root))
        issues.extend(_check_global_blocks(path, root))
        issues.extend(_check_type_settings(path, root))

    return issues


def _check_category_mappings(path: Path, root) -> list[str]:
    issues: list[str] = []
    mappings = child_elements(root, "forecastingCategoryMappings")

    if mappings and len(mappings) != REQUIRED_MAPPING_COUNT:
        issues.append(
            f"{path}: found {len(mappings)} forecastingCategoryMappings occurrences, expected "
            f"{REQUIRED_MAPPING_COUNT}. 'Organizations using either cumulative forecast rollups or "
            "individual forecast category columns must include all eight occurrences of this subtype' "
            "(api_meta 117520)."
        )

    for mapping in mappings:
        name = child_text(mapping, "forecastingItemCategoryApiName")
        if name and name not in ROLLUP_CATEGORY_NAMES:
            issues.append(
                f"{path}: forecastingItemCategoryApiName '{name}' is not a documented rollup type. "
                f"Valid values: {sorted(ROLLUP_CATEGORY_NAMES)} (api_meta 117534)."
            )
        for weighted in child_elements(mapping, "weightedSourceCategories"):
            source = child_text(weighted, "sourceCategoryApiName")
            if source and source not in SOURCE_CATEGORY_NAMES:
                issues.append(
                    f"{path}: sourceCategoryApiName '{source}' under '{name or '<unnamed>'}' is not a "
                    f"documented forecast category. Valid values: {sorted(SOURCE_CATEGORY_NAMES)} "
                    "(api_meta 117969). Note the spaced spellings 'best case' and 'most likely'."
                )
            weight = child_text(weighted, "weight")
            if weight and weight not in ("1.0", "1"):
                issues.append(
                    f"{path}: weight '{weight}' under '{name or '<unnamed>'}' is not supported. "
                    "'The only supported value is 1.0' (api_meta 117981)."
                )
    return issues


def _check_global_blocks(path: Path, root) -> list[str]:
    issues: list[str] = []

    for ranges in child_elements(root, "globalForecastRangeSettings") + child_elements(root, "forecastRangeSettings"):
        period_type = child_text(ranges, "periodType")
        if period_type and period_type not in PERIOD_TYPES:
            issues.append(
                f"{path}: periodType '{period_type}' is not valid. Valid values: {sorted(PERIOD_TYPES)} "
                "(api_meta 117913)."
            )
        displaying = child_text(ranges, "displaying")
        if displaying.isdigit():
            cap = MAX_DISPLAYING_QUARTERS if period_type == "Quarter" else MAX_DISPLAYING_MONTHS
            if int(displaying) > cap:
                issues.append(
                    f"{path}: displaying={displaying} exceeds the documented maximum for periodType "
                    f"'{period_type or 'Month'}'. 'The maximum number of months is 12 and quarters is 8' "
                    "(api_meta 117910)."
                )

    adj_blocks = child_elements(root, "globalAdjustmentsSettings")
    for block in adj_blocks:
        for flag in ("enableAdjustments", "enableOwnerAdjustments", "allowExpandedColumns"):
            if not has_child(block, flag):
                issues.append(
                    f"{path}: globalAdjustmentsSettings is missing required element <{flag}> "
                    "(api_meta 117828 ff -- all three are Required)."
                )
    return issues


def _check_type_settings(path: Path, root) -> list[str]:
    issues: list[str] = []
    type_blocks = child_elements(root, "forecastingTypeSettings")
    active_names: list[str] = []

    for block in type_blocks:
        name = child_text(block, "name") or child_text(block, "masterLabel") or "<unnamed>"
        is_active = child_text(block, "active").lower() == "true"
        if is_active:
            active_names.append(name)

        if has_child(block, "developerName"):
            issues.append(
                f"{path}: forecastingTypeSettings '{name}' contains <developerName>, which is not a field "
                "of ForecastingTypeSettings. Use <name> (the fixed forecast-type string) and <masterLabel> "
                "(api_meta 117722 ff). developerName belongs on ForecastingType."
            )
        if has_child(block, "rollupType"):
            issues.append(
                f"{path}: forecastingTypeSettings '{name}' contains <rollupType>, which does not exist. "
                "The rollup style is expressed by which set of four values appears in "
                "forecastedCategoryApiNames (api_meta 117640)."
            )

        real_name = child_text(block, "name")
        if real_name and real_name not in LEGACY_TYPE_NAMES and "_" not in real_name:
            issues.append(
                f"{path}: forecast type name '{real_name}' is not one of the fixed strings ForecastingSettings "
                "can activate. Territory types use the Territory_Model_NameN form and custom split types use "
                "the split type name; anything else must be authored as a ForecastingType component "
                "(api_meta 117722)."
            )

        date_type = child_text(block, "forecastingDateType")
        if date_type and date_type not in DATE_TYPES:
            issues.append(
                f"{path}: forecastingDateType '{date_type}' on '{name}' is not valid. Valid values: "
                f"{sorted(DATE_TYPES)} (api_meta 117659)."
            )

        # measure coherence
        is_amount = child_text(block, "isAmount").lower()
        is_quantity = child_text(block, "isQuantity").lower()
        if is_amount and is_quantity and is_amount == is_quantity:
            issues.append(
                f"{path}: '{name}' declares isAmount={is_amount} and isQuantity={is_quantity}. "
                "'The value of isAmount is always the opposite of the value of isQuantity' (api_meta 117691)."
            )
        if is_quantity == "true" and is_amount == "true":
            issues.append(
                f"{path}: '{name}' is a quantity forecast type but isAmount is true. A quantity type must "
                "carry isAmount=false, and its quotas load QuotaQuantity rather than QuotaAmount."
            )
        if real_name and "Quantity" in real_name and is_amount == "true":
            issues.append(
                f"{path}: forecast type '{real_name}' is a quantity type by name but declares isAmount=true. "
                "Set isAmount=false / isQuantity=true, or pick the matching Revenue type name."
            )

        if not is_active:
            continue

        issues.extend(_check_category_api_names(path, name, block))

    if len(active_names) > MAX_ACTIVE_FORECAST_TYPES:
        issues.append(
            f"{path}: {len(active_names)} active forecast types ({active_names}); "
            f"'the maximum number of forecast types is four' (api_meta 117503)."
        )
    return issues


def _classify(values: set[str]) -> str | None:
    core = values - EXTRA_FORECASTED
    if core and core <= CUMULATIVE_SET:
        return "cumulative"
    if core and core <= INDIVIDUAL_SET:
        return "individual"
    return None


def _check_category_api_names(path: Path, name: str, block) -> list[str]:
    issues: list[str] = []
    displayed = child_texts(block, "displayedCategoryApiNames")
    forecasted = child_texts(block, "forecastedCategoryApiNames")

    for label, values, allowed in (
        ("displayedCategoryApiNames", displayed, CUMULATIVE_SET | INDIVIDUAL_SET),
        ("forecastedCategoryApiNames", forecasted, CUMULATIVE_SET | INDIVIDUAL_SET | EXTRA_FORECASTED),
    ):
        unknown = sorted(v for v in values if v not in allowed)
        if unknown:
            issues.append(
                f"{path}: active forecast type '{name}' has {label} values {unknown} outside the documented "
                f"enum. Cumulative: {sorted(CUMULATIVE_SET)}. Individual: {sorted(INDIVIDUAL_SET)} "
                "(api_meta 117615 / 117640)."
            )
        if values and len(values) != 4:
            issues.append(
                f"{path}: active forecast type '{name}' has {len(values)} {label} values; the field "
                "'appears four times' (api_meta 117615)."
            )

    if displayed and forecasted and set(displayed) != set(forecasted) - EXTRA_FORECASTED:
        issues.append(
            f"{path}: active forecast type '{name}' has displayedCategoryApiNames {sorted(set(displayed))} "
            f"but forecastedCategoryApiNames {sorted(set(forecasted))}. 'Always use the same 4 values for "
            "both' (api_meta 117617)."
        )

    style = _classify(set(displayed) | set(forecasted))
    if (displayed or forecasted) and style is None:
        issues.append(
            f"{path}: active forecast type '{name}' mixes cumulative and individual category names "
            f"({sorted(set(displayed) | set(forecasted))}). Pick one set of four; mixing them makes the "
            "Enable Cumulative Forecast Rollups org setting ambiguous (api_meta 117655)."
        )

    allowed_adjustable = CUMULATIVE_ADJUSTABLE if style == "cumulative" else INDIVIDUAL_ADJUSTABLE
    for label in ("managerAdjustableCategoryApiNames", "ownerAdjustableCategoryApiNames"):
        values = child_texts(block, label)
        if not values:
            continue
        if len(values) != 2:
            issues.append(
                f"{path}: '{name}' has {len(values)} {label} values; the field 'appears twice' "
                "(api_meta 117703 / 117799)."
            )
        if style and not set(values) <= allowed_adjustable:
            issues.append(
                f"{path}: '{name}' has {label} {sorted(set(values))}, which does not match the {style} "
                f"rollup style. Allowed: {sorted(allowed_adjustable)} (api_meta 117703 / 117799)."
            )

    manager = set(child_texts(block, "managerAdjustableCategoryApiNames"))
    owner = set(child_texts(block, "ownerAdjustableCategoryApiNames"))
    if manager and owner and manager != owner:
        issues.append(
            f"{path}: '{name}' has managerAdjustableCategoryApiNames {sorted(manager)} and "
            f"ownerAdjustableCategoryApiNames {sorted(owner)}. 'If both ... fields are being used, they must "
            "contain the same two values' (api_meta 117710)."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 5: ForecastingType / SourceDefinition / TypeSource / Filter
# ---------------------------------------------------------------------------

def check_forecast_type_components(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    for path in files_named(manifest_dir, "*.forecastingType", "*.forecastingType-meta.xml"):
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        name = child_text(root, "developerName") or path.stem

        role_type = child_text(root, "roleType")
        if role_type and role_type not in ROLE_TYPES:
            issues.append(
                f"{path}: roleType '{role_type}' is not valid. 'Possible values are R (user role-based "
                "forecast type) and Y (Territory2-based forecast type)' (api_meta 75264)."
            )
        if role_type == "Y" and not child_text(root, "territory2Model"):
            issues.append(
                f"{path}: forecast type '{name}' declares roleType=Y (Territory2-based) but has no "
                "<territory2Model>. A territory forecast type needs the name of an active Territory2 model."
            )
        if role_type == "R" and child_text(root, "territory2Model"):
            issues.append(
                f"{path}: forecast type '{name}' declares roleType=R (role-based) but also sets "
                "<territory2Model>. Remove one; the hierarchy is single-valued."
            )

        amount = child_text(root, "amount").lower()
        quantity = child_text(root, "quantity").lower()
        if amount and quantity and amount == quantity:
            issues.append(
                f"{path}: forecast type '{name}' declares amount={amount} and quantity={quantity}. They are "
                "mutually exclusive: amount true means a revenue measure, quantity true a quantity measure "
                "(api_meta 75205 ff)."
            )

        date_type = child_text(root, "dateType")
        if date_type and date_type not in DATE_TYPES:
            issues.append(
                f"{path}: dateType '{date_type}' on '{name}' is not a documented value. Valid values: "
                f"{sorted(DATE_TYPES)} (api_meta 75209). The guide's samples print '0'; that is a retrieval "
                "artefact, not a value to author."
            )

        if child_text(root, "hasCustomGroup").lower() == "true" and not child_text(root, "forecastingGroupDeveloperName"):
            issues.append(
                f"{path}: forecast type '{name}' sets hasCustomGroup=true but has no "
                "<forecastingGroupDeveloperName>, which is 'Required if hasCustomGroup is true' (api_meta 75238)."
            )

    for path in files_named(manifest_dir, "*.forecastingSourceDefinition", "*.forecastingSourceDefinition-meta.xml"):
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        label = child_text(root, "masterLabel") or path.stem

        source_object = child_text(root, "sourceObject")
        if source_object and source_object not in SOURCE_OBJECTS:
            issues.append(
                f"{path}: sourceObject '{source_object}' is not documented. Valid values: "
                f"{sorted(SOURCE_OBJECTS)} (api_meta 75108)."
            )
        date_field = child_text(root, "dateField")
        if date_field and date_field not in DATE_FIELDS:
            issues.append(
                f"{path}: dateField '{date_field}' on '{label}' is not documented. Valid values: "
                f"{sorted(DATE_FIELDS)} (api_meta 75078)."
            )
        user_field = child_text(root, "userField")
        if user_field and user_field not in USER_FIELDS:
            issues.append(
                f"{path}: userField '{user_field}' on '{label}' is not documented. Valid values: "
                f"{sorted(USER_FIELDS)} (api_meta 75129)."
            )
        category_field = child_text(root, "categoryField")
        if category_field and category_field not in CATEGORY_FIELDS:
            issues.append(
                f"{path}: categoryField '{category_field}' on '{label}' is not documented. The only "
                "documented value is Opportunity.ForecastCategoryName (api_meta 75066)."
            )
        territory_field = child_text(root, "territory2Field")
        if territory_field and territory_field not in TERRITORY2_FIELDS:
            issues.append(
                f"{path}: territory2Field '{territory_field}' on '{label}' is not documented. The only "
                "documented value is Opportunity.Territory2Id; 'for user role-based forecast types, this "
                "value is null' (api_meta 75116)."
            )
        measure_field = child_text(root, "measureField")
        if measure_field and not measure_field.startswith(MEASURE_FIELD_PREFIXES):
            issues.append(
                f"{path}: measureField '{measure_field}' on '{label}' does not name a documented source "
                f"object. It must start with one of {list(MEASURE_FIELD_PREFIXES)} (api_meta 75090)."
            )
        if measure_field and source_object and not measure_field.startswith(source_object + "."):
            issues.append(
                f"{path}: measureField '{measure_field}' does not belong to sourceObject '{source_object}' "
                f"on '{label}'. Confirm the pairing against api_meta 75094."
            )

    for path in files_named(manifest_dir, "*.forecastingTypeSource", "*.forecastingTypeSource-meta.xml"):
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        label = child_text(root, "masterLabel") or path.stem
        relation = child_text(root, "relationField")
        if relation and relation not in RELATION_FIELDS:
            issues.append(
                f"{path}: relationField '{relation}' on '{label}' is not documented. Valid values: "
                f"{sorted(RELATION_FIELDS)} (api_meta 75413)."
            )
        if relation and not child_text(root, "parentSourceDefinition"):
            issues.append(
                f"{path}: '{label}' sets relationField but no parentSourceDefinition. The two go together: "
                "relationField 'links the source objects of the parent ForecastingSourceDefinition to the "
                "child ForecastingSourceDefinition' (api_meta 75413)."
            )
        if not child_text(root, "sourceGroup"):
            issues.append(f"{path}: '{label}' has no <sourceGroup>, which is Required (api_meta 75421).")

    filter_conditions: dict[str, int] = {}
    for path in files_named(manifest_dir, "*.ForecastingFilterCondition", "*.ForecastingFilterCondition-meta.xml",
                            "*.forecastingFilterCondition", "*.forecastingFilterCondition-meta.xml"):
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        label = child_text(root, "masterLabel") or path.stem
        operation = child_text(root, "operation")
        if operation and operation not in FILTER_OPERATIONS:
            issues.append(
                f"{path}: operation '{operation}' on '{label}' is not valid. Valid values: "
                f"{sorted(FILTER_OPERATIONS)} (api_meta 74972)."
            )
        if has_child(root, "colName"):
            issues.append(
                f"{path}: '{label}' contains <colName>, which is not a field of ForecastingFilterCondition. "
                "It appears only in the guide's malformed printed sample (api_meta 75006)."
            )
        parent = child_text(root, "forecastingFilter")
        if parent:
            filter_conditions[parent] = filter_conditions.get(parent, 0) + 1

    for parent, count in sorted(filter_conditions.items()):
        if count > MAX_FILTER_CONDITIONS:
            issues.append(
                f"ForecastingFilter '{parent}' has {count} conditions in this manifest. "
                f"'A forecast type can contain up to three filter conditions' (api_meta 75041)."
            )

    for path in files_named(manifest_dir, "*.forecastingFilter", "*.forecastingFilter-meta.xml"):
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue
        logic = child_text(root, "filterLogic")
        if logic and ("OR" in logic.upper().split() or "NOT" in logic.upper().split()):
            issues.append(
                f"{path}: filterLogic '{logic}' uses an unsupported operator. 'Only AND is supported' "
                "(api_meta 74848)."
            )

    return issues


# ---------------------------------------------------------------------------
# Check 6: stage-to-category mapping
# ---------------------------------------------------------------------------

def check_stage_forecast_categories(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    candidates = files_named(
        manifest_dir,
        "OpportunityStage.standardValueSet", "OpportunityStage.standardValueSet-meta.xml",
        "Opportunity.object", "Opportunity.object-meta.xml",
    )
    for path in candidates:
        root, err = parse_xml(path)
        if err:
            issues.append(err)
            continue

        values = []
        for tag in ("standardValue", "picklistValues", "value"):
            for el in root.iter():
                if strip_ns(el.tag) == tag:
                    values.append(el)

        unmapped: list[str] = []
        for value in values:
            full_name = child_text(value, "fullName")
            if not has_child(value, "forecastCategory"):
                # only meaningful for the Stage picklist; skip files that carry other picklists
                if strip_ns(root.tag) == "StandardValueSet":
                    unmapped.append(full_name or "<unnamed>")
                continue
            category = child_text(value, "forecastCategory")
            if category in STAGE_FORECAST_CATEGORIES:
                continue
            hint = STAGE_CATEGORY_ALIASES.get(category)
            if hint:
                issues.append(
                    f"{path}: stage '{full_name}' uses forecastCategory '{category}', which the metadata "
                    f"enum does not accept -- use '{hint}'. Valid values are Omitted, Pipeline, BestCase, "
                    "Forecast, Closed, where 'Forecast' is the category the UI calls Commit (api_meta 47578)."
                )
            else:
                issues.append(
                    f"{path}: stage '{full_name}' uses forecastCategory '{category}', which is not in the "
                    "metadata enum {Omitted, Pipeline, BestCase, Forecast, Closed} (api_meta 47578). There "
                    "is no MostLikely value in this enum."
                )

        if unmapped and strip_ns(root.tag) == "StandardValueSet":
            issues.append(
                f"{path}: {len(unmapped)} opportunity stage value(s) have no <forecastCategory>: "
                f"{unmapped[:8]}{' ...' if len(unmapped) > 8 else ''}. A stage with no forecast category "
                "cannot be placed in any forecast column. Map every stage in the same deploy that adds it."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 7: ForecastingQuota CSV
# ---------------------------------------------------------------------------

def check_quota_csv(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*.csv")):
        lowered = path.name.lower()
        if "quota" not in lowered:
            continue
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.reader(handle)
                header = next(reader, None)
                rows = list(reader)
        except (OSError, csv.Error) as exc:
            issues.append(f"{path}: unreadable CSV -- {exc}")
            continue
        if not header:
            issues.append(f"{path}: quota CSV has no header row.")
            continue

        cols = [(c or "").strip().lower() for c in header]
        colset = set(cols)

        missing = sorted(QUOTA_REQUIRED - colset)
        if missing:
            issues.append(
                f"{path}: ForecastingQuota load is missing required column(s) {missing}. "
                "QuotaOwnerId identifies the quota owner and StartDate places the quota in a period "
                "(object_reference 147887 ff)."
            )
        if "forecastingtypeid" not in colset:
            issues.append(
                f"{path}: no ForecastingTypeId column. Quotas are per forecast type, and a load without it "
                "cannot show attainment against the intended type. Resolve ids with "
                "'SELECT Id, DeveloperName, IsAmount, IsQuantity FROM ForecastingType'."
            )
        for readonly, why in QUOTA_READ_ONLY.items():
            if readonly in colset:
                issues.append(f"{path}: column '{readonly}' must not be loaded -- {why}.")

        measures = QUOTA_MEASURES & colset
        if not measures:
            issues.append(
                f"{path}: neither QuotaAmount nor QuotaQuantity is present. Load exactly one, matching the "
                "forecast type's measure (object_reference 147887 ff)."
            )
        elif len(measures) == 2:
            amount_idx = cols.index("quotaamount")
            quantity_idx = cols.index("quotaquantity")
            both = 0
            for row in rows:
                if len(row) > max(amount_idx, quantity_idx) and row[amount_idx].strip() and row[quantity_idx].strip():
                    both += 1
            if both:
                issues.append(
                    f"{path}: {both} row(s) populate both QuotaAmount and QuotaQuantity. A forecast type is "
                    "either amount-based or quantity-based, never both (object_reference 147946 / 147955); "
                    "split the file per forecast type."
                )
            else:
                issues.append(
                    f"{path}: both QuotaAmount and QuotaQuantity columns are present. Keep only the one that "
                    "matches the forecast type's measure so a mis-mapped column cannot load silently."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 8: forecast-enabled users without a role
# ---------------------------------------------------------------------------

def check_user_csv(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*.csv")):
        lowered = path.name.lower()
        if "user" not in lowered or "quota" in lowered:
            continue
        try:
            with path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                fieldnames = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
                if "forecastenabled" not in fieldnames:
                    continue
                rows = list(reader)
        except (OSError, csv.Error) as exc:
            issues.append(f"{path}: unreadable CSV -- {exc}")
            continue

        role_col = next((f for f in fieldnames if f in ("userroleid", "userrole", "role", "userrole.name")), None)
        if role_col is None:
            issues.append(
                f"{path}: sets ForecastEnabled but carries no role column. For a role-based forecast type a "
                "user with no role has no node in the forecast hierarchy, so ForecastEnabled alone puts "
                "nobody in the forecast. Add UserRoleId to the load and verify it."
            )
            continue

        offenders: list[str] = []
        for row in rows:
            lower = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if lower.get("forecastenabled", "").lower() in ("true", "1", "yes") and not lower.get(role_col):
                offenders.append(lower.get("username") or lower.get("id") or lower.get("email") or "<row>")
        if offenders:
            issues.append(
                f"{path}: {len(offenders)} row(s) set ForecastEnabled=true with an empty role "
                f"({offenders[:5]}{' ...' if len(offenders) > 5 else ''}). In a role-based forecast these "
                "users are enabled but invisible -- they have no node in the hierarchy generated from the "
                "role hierarchy. Assign a role, or use a territory-based forecast type."
            )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_nothing_found(manifest_dir: Path) -> list[str]:
    found = (
        files_named(manifest_dir, "Forecasting.settings", "Forecasting.settings-meta.xml",
                    "ForecastingSettings.settings", "ForecastingSettings.settings-meta.xml",
                    "*.forecastingType", "*.forecastingType-meta.xml",
                    "*.forecastingSourceDefinition", "*.forecastingSourceDefinition-meta.xml",
                    "OpportunityStage.standardValueSet", "OpportunityStage.standardValueSet-meta.xml")
        or [p for p in manifest_dir.rglob("*.csv") if "quota" in p.name.lower()]
    )
    if found:
        return []
    return [
        f"No Collaborative Forecasts artefacts found under {manifest_dir}. Expected any of: "
        "settings/Forecasting.settings-meta.xml, forecastingTypes/*.forecastingType-meta.xml, "
        "forecastingSourceDefinitions/*, standardValueSets/OpportunityStage.standardValueSet-meta.xml, "
        "or a *quota*.csv load file. Retrieve them with: "
        "sf project retrieve start --metadata \"Settings:Forecasting\" ForecastingType "
        "\"StandardValueSet:OpportunityStage\""
    ]


def run_all_checks(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]
    issues: list[str] = []
    issues.extend(check_nothing_found(manifest_dir))
    issues.extend(check_forecasting_settings(manifest_dir))
    issues.extend(check_forecast_type_components(manifest_dir))
    issues.extend(check_stage_forecast_categories(manifest_dir))
    issues.extend(check_quota_csv(manifest_dir))
    issues.extend(check_user_csv(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Collaborative Forecasts metadata and quota/user load files against the Metadata API "
            "Developer Guide and Object Reference. Point --manifest-dir at force-app/main/default or the "
            "root of a retrieved package."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument("--quiet", action="store_true", help="Print issues only, no header.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not args.quiet:
        print(f"Checking Collaborative Forecasts artefacts in: {manifest_dir}\n")

    issues = run_all_checks(manifest_dir)

    if not issues:
        if not args.quiet:
            print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}\n")
    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
