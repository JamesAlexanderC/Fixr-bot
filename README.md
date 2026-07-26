# Fixr-Bot by James Clarke

This is a comprehensive reliable open solution to reserving any ticket on the https://fixr.co website.

## Usage

For legal reasons this bot will not automate checkout, simply reserve a ticket for a selected event and send a configurable push notifaction upon reservation

Obviously this bot will need to be always-on, a docker image is the intended final ditributable form, which will be easily run and expose a configuration interface

## Architecture

This program uses the wrapper Camoufox around playwright to enable automation.

The two main running process are an API exposing commands and allowing communcation, and an engine which runs camoufox workers

## Development

Release 1.0 planned for 09/2026