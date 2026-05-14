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
            circuit.importQASM(cleanQasm(payload.qasm));

        let result;

        switch (payload.target) {
            case "qiskit":
                result = circuit.exportQiskit( {},
                    false,
                    null,
                    null);
                break;
            case "cirq":
                result = circuit.exportCirq();
                break;
            case "qasm":
                result = circuit.exportQASM();
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