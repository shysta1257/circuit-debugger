# Circuit Debugger

When a breadboard project doesn't work, it's often a wrong connection that's really hard to spot by eye. The idea: take a photo of your circuit, and the tool works out what's on the board, rebuilds the connections, and tells you what's likely wrong.

## Plan
1. **Component detection:** train a YOLO model to detect components on a breadboard (resistors, LEDs, wires, ICs, power), using my own labelled photos
2. **Connection mapping:** map detected parts onto breadboard rows and rails to reconstruct which components are connected
3. **Checks + advice:** rule-based checks (LED without a resistor, short across rails, reversed polarity) with plain-English explanations

## Status
🚧 Just started, work in progress.
