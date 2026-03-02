async function getResult() {
    const response = await fetch('http://127.0.0.1:8000/result');
    const json = await response.json();
    let size = Object.keys(json).length;
    for (let i = 0; i < size; i++) {
        console.log(json[i]);
        let box_json = json[i];
        //result-box
        let center_div = document.getElementById('center-div-id')
        let element = document.createElement('div');
        element.id = 'result-box'+ i;
        element.className = 'result-box';
        center_div.appendChild(element);
        
        //file path
        let result_box = document.getElementById('result-box' + i)
        element = document.createElement('div');
        element.id = 'file-path'+ i;
        element.className = 'file-path';
        result_box.appendChild(element);
        document.getElementById('file-path' + i).innerHTML += box_json["file-path"];

        //file name
        element = document.createElement('div');
        element.id = 'file-name'+ i;
        element.className = 'file-name';
        result_box.appendChild(element);
        document.getElementById('file-name' + i).innerHTML += box_json["file-name"];

        // timestamp
        element = document.createElement('div');
        element.id = 'timestamp'+ i;
        element.className = 'timestamp';
        result_box.appendChild(element);

        // start and end
        let timestamp = document.getElementById('timestamp' + i)
        // start
        element.id = 'start'+ i;
        element.className = 'start time-dec';
        timestamp.appendChild(element);
        document.getElementById('start' + i).innerHTML += box_json["start"];
    }
    
}
getResult()