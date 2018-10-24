/*****************************************************************************
 * FILE:    utilities.js
 * DATE:    October, 19, 2018
 * AUTHOR:  Nathan Swain
 * COPYRIGHT: (c) Aquaveo 2018
 * LICENSE:
 *****************************************************************************/
function contains(str, sub) {
    if (str.indexOf(sub) === -1) {
        return false;
    }
    return true;
}

function in_array(item, array) {
    return array.indexOf(item) !== -1;
}

function is_defined(variable) {
    return !!(typeof variable !== typeof undefined && variable !== false);
}

function to_title_case(str) {
    return str.replace(/\w+/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

function var_to_title_case(str) {
    str = str.replace(/_/ig, ' ');
    return to_title_case(str);
};