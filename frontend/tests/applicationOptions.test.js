import assert from "node:assert/strict";
import test from "node:test";

import {
  applicationTypeOptions,
  parcelFieldOptions,
  zoneOptions
} from "../src/data/options.js";

test("application types have readable labels and stable API values", () => {
  assert.deepEqual(applicationTypeOptions, [
    { value: "first_registration", label: "First Registration" },
    { value: "ownership_transfer", label: "Ownership Transfer" },
    { value: "parcel_subdivision", label: "Parcel Subdivision" },
    { value: "parcel_merge", label: "Parcel Merge" },
    { value: "boundary_correction", label: "Boundary Correction" },
    { value: "certificate_request", label: "Certificate Request" }
  ]);
});

test("parcel fields have readable labels", () => {
  assert.deepEqual(parcelFieldOptions, [
    { key: "parcel_number", label: "Parcel Number" },
    { key: "block_number", label: "Block Number" },
    { key: "basin_number", label: "Basin Number" },
    { key: "area_sqm", label: "Area (Square Meters)", inputMode: "decimal" }
  ]);
});

test("zones use readable labels and stable API values", () => {
  assert.deepEqual(zoneOptions, [
    { value: "ZONE-RM-01", label: "Ramallah Zone 1" },
    { value: "ZONE-RM-02", label: "Ramallah Zone 2" }
  ]);
});
