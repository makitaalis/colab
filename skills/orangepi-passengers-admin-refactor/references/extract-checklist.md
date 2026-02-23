# Extract Checklist

## Before extraction

- route list and endpoint signatures captured;
- response schemas captured from live curl;
- role checks and audit paths identified.

## During extraction

- move pure logic first;
- keep old route names and params;
- do not change default limits/filters.

## After extraction

- py_compile + compileall pass;
- smoke API and UI pass;
- docs updated with new module file path.
