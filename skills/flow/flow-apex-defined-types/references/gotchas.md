# Gotchas — Apex-Defined Types

## 1. Missing `@AuraEnabled` Silently Hides Field

Fields without `@AuraEnabled` do not appear in Flow. No error — they are
invisible.

## 2. Maps Are Not Supported

Flow cannot bind a `Map<>` attribute. Model as `List<KeyValue>`.

## 3. Renaming A Field Breaks Flow

The Flow references the field by name. Renaming is a silent breaking
change — the Flow keeps the old name until re-edited.

## 4. Nested Apex-Defined Types Must Also Be `@AuraEnabled` End-To-End

A parent class with all `@AuraEnabled` fields is still broken if a child
Apex class it references has a non-`@AuraEnabled` field — that field is
just missing in Flow.

## 5. Lists Of Primitives vs Collection

`List<String>` inside an Apex-Defined Type is fine. Flow treats it as a
collection of text inside the typed variable.

## 6. Datetime Serialisation Quirks

Apex `Datetime` serialises in GMT. If the upstream API sends a local
time, parse explicitly before assigning. Flow displays as the org's user
time zone.

## 7. Constructor With Arguments Breaks Instantiation From Flow

Flow does not call constructors. A class with a required-arg constructor
cannot be built from Flow — only from Apex before passing in. Use a
no-arg constructor if Flow needs to build instances.

## 8. Managed Package Namespace

An Apex-Defined Type from a managed package is referenced with the
namespace prefix in Flow. Unpacked changes that remove the namespace
break the binding.
