$(document).ready(function()

    {
	var x = 0; //Initial field counter
	var list_maxField = 10; //Input fields increment limitation
        //Once add button is clicked
	$('.list_add_button').click(function()
	    {
	    //Check maximum number of input fields
	    if(x < list_maxField){ 
	        x++; //Increment field counter
	        var list_fieldHTML = '<div class="row"><div class="col-xs-4 col-sm-4 col-md-4"><div class="form-group"><br><input name="percent['+x+']" type="text" placeholder="%" class="form-control"/></div></div><div class="col-xs-4 col-sm-4 col-md-4"><div class="form-group"><br><input name="amount['+x+']" type="text" placeholder="$$" class="form-control"/></div></div><div class="col-xs-1 col-sm-7 col-md-1"><br><a href="javascript:void(0);" class="list_remove_button btn btn-danger ">-</a></div></div>'; //New input field html 
	        $('.list_wrapper').append(list_fieldHTML); //Add field html
	    }
        });

        //Once remove button is clicked
        $('.list_wrapper').on('click', '.list_remove_button', function()
        {
           $(this).closest('div.row').remove(); //Remove field html
           x--; //Decrement field counter
        });
});


