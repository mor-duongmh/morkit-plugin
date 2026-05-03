#!/usr/bin/env bash
# Minimal assertion helpers for bash tests in this plugin.
# Source this file from any test-*.sh script.
set -euo pipefail

assert_equal() {
    local actual="$1" expected="$2" label="${3:-equality}"
    if [[ "$actual" != "$expected" ]]; then
        echo "FAIL ($label): expected '$expected' got '$actual'" >&2
        exit 1
    fi
}

assert_contains() {
    local haystack="$1" needle="$2" label="${3:-substring}"
    if [[ "$haystack" != *"$needle"* ]]; then
        echo "FAIL ($label): '$haystack' does not contain '$needle'" >&2
        exit 1
    fi
}

assert_file_exists() {
    local path="$1" label="${2:-file exists}"
    if [[ ! -f "$path" ]]; then
        echo "FAIL ($label): file '$path' does not exist" >&2
        exit 1
    fi
}

assert_dir_exists() {
    local path="$1" label="${2:-dir exists}"
    if [[ ! -d "$path" ]]; then
        echo "FAIL ($label): directory '$path' does not exist" >&2
        exit 1
    fi
}

assert_file_not_exists() {
    local path="$1" label="${2:-file absent}"
    if [[ -f "$path" ]]; then
        echo "FAIL ($label): file '$path' should not exist" >&2
        exit 1
    fi
}
