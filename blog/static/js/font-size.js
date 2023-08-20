let parent = document.querySelector('fieldset.module.aligned')

let row = document.createElement('div')
row.classList.add('form-row')

row.appendChild(document.createElement('div'))
parent.appendChild(row)

row = row.querySelector('div')
row.classList.add('flex-container')

let label = document.createElement('label')
label.innerText = 'Font Size'

row.appendChild(label)

let button = document.createElement('button')
button.innerText = '-'
button.classList.add('neg')

var fontSize = 12.5

button.addEventListener('click', e => {
    e.preventDefault()
    fontSize = fontSize > 1 ? fontSize - 1 : fontSize

    let textareas = document.querySelectorAll('.textarea')
    textareas.forEach(textarea => {
        textarea.style.fontSize = `${fontSize}px`
    })
})



row.appendChild(button)

button = document.createElement('button')
button.innerText = '+'
button.classList.add('pos')

button.addEventListener('click', e => {
    e.preventDefault()
    fontSize = fontSize > 1 ? fontSize + 1 : fontSize

    let textareas = document.querySelectorAll('.textarea')
    textareas.forEach(textarea => {
        textarea.style.fontSize = `${fontSize}px`
    })
})

row.appendChild(button)

button.click()