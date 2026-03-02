// Please dont touch this file, took me hours

// Send the form data to the fastapi server /query
var form = document.getElementById('search-form');
form.onsubmit = function(event){
        var formData = new FormData(form);
        const response = fetch("http://127.0.0.1:8000/query", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
            },
            body: JSON.stringify(Object.fromEntries(formData)),
            })
        window.location.replace("search.html");
        //Fail the onsubmit to avoid page refresh.
        return false; 
    }