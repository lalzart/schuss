# Non-musical smoke state matrix

The fixture owns only an accepted normalized test value, accepted-event count,
and reset count. A supported three-byte message updates the value; malformed or
unassigned messages do not. Reset clears value and event count and increments
the reset count. No musical, source-equivalence, device, or lifecycle meaning
is attached to these states.
