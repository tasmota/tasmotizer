@ECHO OFF
SETLOCAL EnableExtensions 

SET PROGRAM-NAME=tasmotizer
SET FILE-NAME=tasmotizer
SET LANGUAGE-LIST=it

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Convert PO files in MO fiels 
ECHO ********************************************************
ECHO.
ECHO.
ECHO            #### Press any key to continue ####
ECHO            ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Convert PO files in MO fiels 
ECHO ********************************************************
ECHO.
ECHO.
for %%x in (%LANGUAGE-LIST%) do (
   IF EXIST  ..\locale\%%x\lc_messages\%FILE-NAME%.po (
      ECHO **** Country = %%x - Compiling '%FILE-NAME%.po' in '%FILE-NAME%.mo'....
      msgfmt ..\locale\%%x\lc_messages\%FILE-NAME%.po -o ..\locale\%%x\lc_messages\%FILE-NAME%.mo
   )
)

ECHO.
ECHO.
ECHO      **** Press any key to exit ****

pause >NUl
SET PROGRAM-NAME=
SET FILE-NAME=
SET LANGUAGE-LIST=
