$(document).ready(function() {


	$('.rango-add').click(function(){
		alert("click huurd.");
		var catid = $(this).attr("data-catid");
		alert(catid);
		var url = $(this).attr("data-url");
		alert(url);
		var title = $(this).attr("data-title");
		alert(title);
		var me = $(this);
		alert(me);
			$.get('/rango/auto_add_page/', {category_id : catid, url : url, title: title}, function(data){
					$('#pagesz').html(data);
					console.log("we got the new page...");
				});
		});


	$('#likes').click(function(){
			alert("You liked")
	        var catid;
	        catid = $(this).attr("data-catid");
	         $.get('/rango/like_category/', {category_id: catid}, function(data){
	                   $('#like_count').html(data);
	                   $('#likes').hide();
	               });
	    });

	$('#suggestion').keyup(function(){
	        var query;
	        query = $(this).val();
	         $.get('/rango/suggest_category/', {suggestion: query}, function(data){
	                  $('#cats').html(data);
	               });
	    });


});