var img_per_page = 5
var current_page = 0
var total_page = -Math.floor(-images.length / img_per_page)
function insertImages(pagenum) {
	var end = Math.min((pagenum + 1) * img_per_page, images.length)
	var oldimages = document.getElementById('image-content')
	document.body.removeChild(oldimages)
	var bottom = document.getElementById('image-bottom')
	var newimages = document.createElement('div')
	newimages.setAttribute('id', 'image-content')
	for (var i = pagenum * img_per_page; i < end; ++i) {
		var img = document.createElement('img')
		img.setAttribute('src', images[i])
		img.setAttribute('alt', 'image')
		img.setAttribute('class', 'image')
		newimages.appendChild(img)
	}
	document.body.insertBefore(newimages, bottom)
}
function prev() {
	current_page--;
	if (current_page >= 0)
		insertImages(current_page)
	else
		current_page = 0
	updatePageinfo()
}
function next() {
	current_page++;
	if (current_page < total_page)
		insertImages(current_page)
	else
		current_page = total_page - 1
	updatePageinfo()
}
function gotoPage(inputstr) {
	var pagenum = parseInt(inputstr, 10)
	if (pagenum < 1 || pagenum > total_page) return;
	if (current_page == pagenum - 1) return;
	current_page = pagenum - 1
	updatePageinfo()
	insertImages(pagenum - 1)
}
function updatePageinfo() {
	var pageinfo = document.getElementById('pageinfo')
	pageinfo.innerHTML = 'current page: ' + (current_page + 1) + ' / ' + total_page
}
updatePageinfo()
insertImages(0)
var userAgent = navigator.userAgent;
var isChrome = userAgent.indexOf('Chrome') > -1
var isSafari = userAgent.indexOf('Safari') > -1
function goTop() {
	timer = setInterval(function () {
		var backtop = document.documentElement.scrollTop //速度操作  减速
		var speedtop = backtop / 5
		document.documentElement.scrollTop = backtop - speedtop  //高度不断减少
		if(backtop == 0){  //滑动到顶端
			clearInterval(timer);  //清除计时器
		}
	}, 30)
}