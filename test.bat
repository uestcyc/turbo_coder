@echo off

if [%1] EQU [html] (
    nosetests tests --with-coverage --cover-erase --cover-html
    start cover\index.html /min
) else (
    nosetests tests --with-coverage --cover-erase
)
