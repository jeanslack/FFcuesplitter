REM GENRE "Electronic"
REM DATE 2025
REM COMMENT "Test with "malformed COMMENT" and 'some' malformed 'TITLE""
PERFORMER "Sox ASCII"
TITLE "Test Samples ASCII"
FILE "Three Samples.flac" WAVE
  TRACK 01 AUDIO
    TITLE "This is a 'Malformed title'"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Another two seconds of "malformed TITLE""
    INDEX 01 00:02:00
  TRACK 03 AUDIO
    TITLE ""Again? Yes", 'unfortunately', "another malformed" title."
    INDEX 01 00:04:00
