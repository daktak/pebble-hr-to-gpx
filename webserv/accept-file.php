<?php
$currentdir = getcwd();
$target = $currentdir .'/uploads/health.csv';
$fp = fopen($target,'a');
fwrite($fp,$_POST['key']);
fclose($fp); 
?>
