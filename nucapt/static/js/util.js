/**
 * Initialize a table to be able to automatically add and remove rows from a "KeyValueField"
 * @param tableName Name of table in which form is stored
 * @param fieldTitle Title of field (ex: "misc" for inputs named "misc-0-key")
 */
var keyValueTable = function (tableName, fieldTitle) {
    // Handle adding/removing metadata rows
    var getNumRows = function () {
        return $("#" + tableName).find("tr").length - 1;
    };
    if (getNumRows() === 0) {
        $("#" + tableName + "_btn-del-row").hide();
    }

    $("#" + tableName + "_btn-add-row").click(function () {
        var numRows = getNumRows();

        // Make a new form row
        var tr = document.createElement("tr");
        ['key', 'value'].forEach(function (e) {
            var td = document.createElement("td");
            var input = document.createElement("input");
            input.id = fieldTitle + '-' + numRows + "-" + e;
            input.name = input.id;
            input.type = 'text';
            td.appendChild(input);
            tr.appendChild(td)
        });
        var td = document.createElement("td");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.onclick = function () {
            this.parentNode.parentNode.remove();
        };
        btn.className = "btn-sm btn-danger";
        btn.innerHTML = "Delete";
        td.appendChild(btn);
        tr.appendChild(td);
        $("#" + tableName + " tr:last").after(tr);
    });
};
