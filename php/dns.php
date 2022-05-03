<?php

 $hostnameip = $_GET['dns'];
 $x = gethostbyname('$hostnameip'); 
 echo $x;

?>