/*
A comment.
*/
function CountCBs(my) {
    var children, count, firstnode, i;

    if (my == null) {
        firstnode=document.getElementById("AllHosts");
        count = CountCBs(firstnode);
        document.getElementById("B3").value = "Refresh selected resources (" + count + ")";
        }
    else {
        count = 0;
//        if (my.tagName == "INPUT" && my.attributes[0].nodeValue == "checkbox") {
        if (my.tagName == "INPUT" && my.type == "checkbox") {
            if (my.checked == true) {
                count = 1;
                }
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            count += CountCBs(children[i]);
            }

        return count;
        }
}

function DisableAll(my) {
    var children, firstnode, i;

    if (my == null) {
        firstnode=document.getElementById("options-section");
        DisableAll(firstnode);
        }
    else {
        if (my.tagName == "INPUT") {
            my.disabled = true;
            my.name = "disabled"
            my.blur();
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            DisableAll(children[i]);
            }
        return;
        }
}

function DisableDisabled(my) {
    var children, firstnode, i;

    if (my == null) {
        firstnode=document.getElementById("options-section");
        DisableDisabled(firstnode);
        }
    else {
        if (my.tagName == "INPUT" && my.name == "disabled") {
            my.disabled = true;
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            DisableDisabled(children[i]);
            }
        return;
        }
}

function EnableDisable(id1,id2) {
    if (document.getElementById(id1).disabled == true) {
        document.getElementById(id1).disabled = false;
        document.getElementById(id1).name = id1
        document.getElementById(id1).focus();
        }
    else {
        document.getElementById(id1).disabled = true;
        document.getElementById(id1).name = "disabled"
        document.getElementById(id1).blur();
        }

    if (id1 == id2 || document.getElementById(id1).disabled == true)
        return;

    document.getElementById(id2).name = "disabled"
    document.getElementById(id2).disabled = true;
    document.getElementById(id2).blur();
    return;
}

function FormReset() {
    UnSetCBs();
    DisableAll();
    FormSubmit();
}

function FormSubmit(button_type) {
    SetH2();
    if (document.getElementById("ta").disabled == false) {
        document.getElementById("ta").value = TimeConvert(document.getElementById("ta").value, 'seconds');
    }

    if (button_type != "submit") {
        document.getElementById("ShowByHostForm").submit();
    }
}

function OptionHelp(msg) {
    alert(msg);
}

function SetCBs(my) {
    var cbs, i;

    if (document.getElementById("h2").value != "") {
        cbs = document.getElementById("h2").value.split("_");
        for (i=0;i<cbs.length;i++) {
            document.getElementById(cbs[i]).checked = true;
        }
    }
}

function SetH2(my) {
    var children, firstnode, h2_string = '', h2_string_child,  i;

    if (my == null) {
        firstnode=document.getElementById("AllHosts");
        document.getElementById("h2").value = SetH2(firstnode);
        }
    else {
        if (my.tagName == "INPUT" && my.type == "checkbox") {
            if (my.checked == true) {
                h2_string = my.id;
                }
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            h2_string_child = SetH2(children[i]);
            if (h2_string_child != '') {
                if (h2_string == '') {
                    h2_string = h2_string_child; 
                    }
                else {
                    h2_string += "_" + h2_string_child;
                    }
                }
            }
        return h2_string;
        }
}

function TimeAdjust(opt) {
    document.getElementById("ta").disabled = false;
    document.getElementById("ta").name = "ta"

    document.getElementById("tr").disabled = false;
    document.getElementById("tr").name = "tr"

    var h3 = new Number(document.getElementById("h3").value);
    var ta = new Number(TimeConvert(document.getElementById("ta").value, "seconds"));
    var tr = new Number(document.getElementById("tr").value);
    var new_ta, new_tr;

    if (opt == 'tad') {
        ta=ta-(3600*tr/2);
        }
    else if (opt == 'trd') {
        tr=tr/2;
        }
    else if (opt == 'tru') {
        tr=tr*2;
        }
    else if (opt == 'tau') {
        ta=ta+(3600*tr/2);
        }
    else {
        return;
        }

    if ((ta + (3600 * tr)) > h3) {
        ta = h3 - (3600 * tr);
        }

    document.getElementById("ta").value = TimeConvert(ta, "date");
    document.getElementById("tr").value = tr.toString();
    FormSubmit('button');
}

function TimeConvert(time, opt) {
    if (opt == 'seconds') {
        var dta = new Date(time);
        return dta.getTime() / 1000;
    } else {
        var dta = new Date(time*1000);
        return dta.toString();
    }
}

function ToggleChildCBs(pid, my) {
    var children, firstnode, i, parent_id;

    if (my == null) {
        firstnode=document.getElementById("AllHosts");
        ToggleChildCBs(pid, firstnode);
        CountCBs();
        }
    else {
//        if (my.tagName == "INPUT" && my.attributes[0].nodeValue == "checkbox") {
        if (my.tagName == "INPUT" && my.type == "checkbox") {
            parent_id = pid + "."
            if (my.id.length > parent_id.length) {
                if (my.id.slice(0, parent_id.length) == parent_id) {
                    my.checked = document.getElementById(pid).checked
                    }
                }
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            ToggleChildCBs(pid, children[i]);
            }

        return;
        }
}

function ToggleDisplay(id) {
    var element;

    element = document.getElementById(id);
    if (element.style.display == '' || element.style.display == 'block')
        element.style.display = 'none';
    else
        element.style.display = 'block';

    return;
}

function UnSetCBs(my) {
    var children, firstnode, i;

    if (my == null) {
        firstnode=document.getElementById("AllHosts");
        UnSetCBs(firstnode);
        }
    else {
//        if (my.tagName == "INPUT" && my.attributes[0].nodeValue == "checkbox") {
        if (my.tagName == "INPUT" && my.type == "checkbox") {
            my.checked = false;
            }

        children = my.childNodes;
        for (i=0;i<children.length;i++) {
            UnSetCBs(children[i]);
            }
        }
}
