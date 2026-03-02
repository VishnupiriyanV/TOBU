async function getResult() {
    const response = await fetch('http://127.0.0.1:8000/result');
    const json = await response.json();
    let size = Object.keys(json).length;
    if (size>0) {
    for (let i = 0; i < size; i++) {
        let box_json = json[i];
        //result-box
        let center_div = document.getElementById('center-div-id')
        let element = document.createElement('div');
        element.id = 'result-box'+ i;
        element.className = 'result-box';

        //append result box
        center_div.appendChild(element);
        
        //file path
        let result_box = document.getElementById('result-box' + i)
        let fp_element = document.createElement('div');
        fp_element.id = 'file-path'+ i;
        fp_element.className = 'file-path';

        //append fp div and content
        result_box.appendChild(fp_element);
        document.getElementById('file-path' + i).innerHTML += box_json["file-path"];

        //file name
        let fn_element = document.createElement('div');
        fn_element.id = 'file-name'+ i;
        fn_element.className = 'file-name';

        //append fn div and contents
        result_box.appendChild(fn_element);
        document.getElementById('file-name' + i).innerHTML += box_json["file-name"];

        // timestamp
        let ts_element = document.createElement('div');
        ts_element.id = 'timestamp'+ i;
        ts_element.className = 'timestamp';
        result_box.appendChild(ts_element);

        // start and end
        let timestamp = document.getElementById('timestamp' + i)
        // start
        let start_element = document.createElement('div');
        start_element.id = 'start'+ i;
        start_element.className = 'start time-dec';
        timestamp.appendChild(start_element);
        document.getElementById('start' + i).innerHTML += box_json["start"];

        // end
        let end_element = document.createElement('div');
        end_element.id = 'end'+ i;
        end_element.className = 'end time-dec';
        timestamp.appendChild(end_element);
        document.getElementById('end' + i).innerHTML += box_json["end"];

        //result-text
        let result_element = document.createElement('div');
        result_element.id = 'result-text'+ i;
        result_element.className = 'result-text';
        result_box.appendChild(result_element);
        document.getElementById('result-text' + i).innerHTML += box_json["text"];
    }
}   else {
    randomImage();
}
    
}

function randomImage() {
    let error_div = document.getElementById('error');
    let img = document.createElement("img");
    img.className = 'error-img';
    img.src = 'imgs/no-result/error-' + getRndInteger(1,4) + '.png'
    error_div.appendChild(img);
    let error_text =  document.createElement("div");
    error_text.id = "no-result";
    error_text.className = "no-result";
    error_div.appendChild(error_text);
    document.getElementById('no-result').innerHTML += "No results found :/";
    
}

function getRndInteger(min, max) {
  return Math.floor(Math.random() * (max - min + 1) ) + min;
}

getResult()