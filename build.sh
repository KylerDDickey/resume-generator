#!/bin/sh

TODAY=$(date '+%Y-%m-%d')

pandoc doc.md -o kdd_resume_$TODAY.pdf
