@ECHO OFF
SETLOCAL EnableExtensions 

SET PROGRAM-NAME=tasmotizer
SET FILE-NAME=tasmotizer
SET LANGUAGE-LIST=it

SET CHARACTERS=400
SET MSGMERGE-OPTIONS=-q -U -N --backup=none --width=%CHARACTERS% --no-wrap --no-location
SET MSGATTRIB-OPTIONS=--no-obsolete --no-fuzzy --width=%CHARACTERS% --no-wrap --no-location
SET MSGFMT-OPTIONS=--statistics

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Update language files using master template 
ECHO ********************************************************
ECHO.
ECHO.
ECHO            #### Press any key to continue ####
ECHO            ####   Press CTRL+C to break   ####
PAUSE >NUL

CLS
ECHO ********************************************************
ECHO * %PROGRAM-NAME%
ECHO * Update language files using master template 
ECHO ********************************************************
ECHO.
ECHO *******************************************************

for %%x in (%LANGUAGE-LIST%) do (

   IF EXIST ..\locale\%%x\lc_messages\%FILE-NAME%.po (
      ECHO **** Country = %%x - Merging '%FILE-NAME%.po' with '%FILE-NAME%.pot' template....
      msgmerge %MSGMERGE-OPTIONS% ..\locale\%%x\lc_messages\%FILE-NAME%.po ..\locale\%FILE-NAME%.pot >NUL

      ECHO **** Country = %%x - Cleaning obsolete entries from '%FILE-NAME%.po'....
      msgattrib %MSGATTRIB-OPTIONS% ..\locale\%%x\lc_messages\%FILE-NAME%.po > ..\locale\%%x\lc_messages\%FILE-NAME%_new.po

      copy ..\locale\%%x\lc_messages\%FILE-NAME%_new.po ..\locale\%%x\lc_messages\%FILE-NAME%.po >NUL
      del ..\locale\%%x\lc_messages\%FILE-NAME%_new.po >NUL

      ECHO **** Country = %%x - Statistics about '%FILE-NAME%.po'....
      msgfmt %MSGFMT-OPTIONS% ..\locale\%%x\lc_messages\%FILE-NAME%.po

      ECHO *******************************************************
      ECHO.
   )
)

if exist Messages.mo del Messages.mo > NUL

ECHO.
ECHO.
ECHO      #### Press any key to exit #####
PAUSE > NUL

SET MSGMERGE.OPTIONS=
SET MSGATTRIB.OPTIONS=
SET MSGFMT.OPTIONS=
SET LANGUAGE-LIST=

