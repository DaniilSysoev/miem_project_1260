select = document.querySelector('select')
select.addEventListener('change', (event) => {
    window.location.href = '/index/' + event.target.value
})

checkbox = document.querySelector('input[type="checkbox"]')
checkbox.addEventListener('change', (event) => {
    console.log(true)
    document.querySelector('#printer_name').submit()
})