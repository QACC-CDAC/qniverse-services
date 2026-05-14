const QuantumCircuit = require("quantum-circuit");

let input = "";

function cleanQasm(qasm) {
    return qasm
        .split("\n")
        .map(line => line.split("//")[0].trim()) // remove inline comments
        .join("\n");
}

process.stdin.on("data", chunk => input += chunk);

process.stdin.on("end", () => {
    try {
        const payload = JSON.parse(input);

            const circuit = new QuantumCircuit();
            circuit.importQASM(payload.qasm);

        let result;

        switch (payload.target) {
            case "qiskit":
                result = circuit.exportToQiskit( {},
                    false,
                    null,
                    null);
                break;
            case "cirq":
                result = circuit.exportToCirq({},false);
                break;
            case "qasm":
                result = circuit.exportToQASM({}, false);
                break;
            case "quil":
                result = circuit.exportToQuil({}, false);
                break;
            case "cudaq":
                result = circuit.exportToCudaQ({}, false);
                break;
            case "qulacs":
                result = circuit.exportToQulacs({}, false);
                break;
            case "quest":                
                result = circuit.exportToQuest({}, false);
                break;
            case "rigetti":
                result = circuit.exportToRigetti({}, false);
                break;
            case "qi":
                result = circuit.exportToQI({}, false);
                break;
            default:
                result = "Unsupported target";
        }

        console.log(result);
    } catch (err) {
        console.error("ERROR:", err.message);
        process.exit(1);
    }
});
