<?php
$currentdir = getcwd();
$target = $currentdir .'/uploads/health.csv';
$fp = fopen($target,'a');
if ( !preg_match('/,0$/',$_POST['key']) ) {
  fwrite($fp,$_POST['key']);
  fwrite($fp,"\n");
}
fclose($fp); 
?>
