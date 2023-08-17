var textAreas = document.querySelectorAll('textarea')
var form = document.querySelectorAll('form')[1]

for (const textArea of textAreas) {
    textArea.classList.add('invisible')

    let parent = textArea.parentElement
    let newElement = document.createElement('div')

    newElement.classList.add('textarea')
    newElement.contentEditable = 'true'

    newElement.innerText = textArea.value

    parent.appendChild(newElement)
}

form.addEventListener('submit', (e) => {
    for (const textArea of textAreas) {
        let div = textArea.parentElement.querySelector('div.textarea')
        div.innerHTML = div.innerHTML.replace(/&nbsp;/g, '')
        textArea.value = div.innerText
    }
})

function format(html) {
    var tab = '\t\t\t\t';
    var result = '';
    var indent = '';

    html.split(/>\s*</).forEach(function (element) {
        if (element.match(/^\/\w/)) {
            indent = indent.substring(tab.length);
        }

        result += indent + '<' + element + '>\r\n';

        if (element.match(/^<?\w[^>]*[^\/]$/) && !element.startsWith("input")) {
            indent += tab;
        }
    });

    return result.substring(1, result.length - 3);
}

var divs = document.querySelectorAll('div.textarea')

for (const div of divs) {
    let text = format(div.innerText)

    let arr = text.split(new RegExp(/\.[\s\n]/g)).filter(val => val ? true : false)
    let trimmed_arr = arr.map(x => x.trim().replace(new RegExp(/[\s\.]/g), ''))

    div.innerHTML = ''
    trimmed_arr.forEach((value, index, array) => {
        let element = null, text = arr[index]

        if (array.indexOf(value) != index) {
            element = document.createElement('span')
            element.classList.add('highlight')
        }

        if (index < array.length - 1) {
            text += '. '
        }

        if (element) {
            element.innerText = text
        }

        element = element ?? document.createTextNode(text)

        div.appendChild(element)
    })
}

for (const div of divs) {
    let text = div.innerHTML

    let arr = text.split('\n')

    div.innerHTML = ''
    arr.forEach((value, index, array) => {
        let parent = document.createElement('span')
        parent.innerHTML = value

        if (index < array.length - 1) {
            parent.appendChild(document.createElement('br'))
        }

        div.appendChild(parent)
    })
}

for (const div of divs) {
    div.innerHTML = div.innerHTML.replace(/[\t]/g, '&nbsp;')
}