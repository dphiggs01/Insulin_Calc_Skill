#!/usr/bin/env bash

# prior to using this bash script you must first configure the
# aws cli and set the region appropriately

#assume the current directory name is the name for the skill function
SKILL_NM=${PWD##*/}

SKILL_DIR=${PWD}
SKILLS_FRAMEWORK_DIR=../../skill_fwk

SKILL_ZIP=alexa_skill.zip


function create_source_zip {
   cd $SKILLS_FRAMEWORK_DIR
   zip -r $SKILL_DIR/$SKILL_ZIP *.py *.json
   cd $SKILL_DIR
   zip -r $SKILL_DIR/$SKILL_ZIP *.py *.json
}

function update_function {
  aws lambda update-function-code \
     --region us-east-1 \
     --function-name $SKILL_NM  \
     --zip-file fileb://$SKILL_ZIP \
     --profile adminuser
}

function create_function {
  aws lambda create-function \
     --function-name $SKILL_NM \
     --runtime python3.6 \
     --role arn:aws:iam::280056172273:role/AlexaLambdaRole \
     --handler lambda_function.lambda_handler \
     --description $SKILL_NM \
     --timeout 3 \
     --memory-size 128 \
     --zip-file fileb://$SKILL_ZIP \
	> /dev/null
}

function add_trigger {
  aws lambda add-permission \
     --function-name $SKILL_NM \
     --statement-id "alexa_trigger" \
     --action "lambda:InvokeFunction" \
     --principal "alexa-appkit.amazon.com"
}  


#create the source zip file
create_source_zip

#attempt to update the lambda function
update_function

#if update fails assume you need to create the function
if [ "$?" != "0" ]; then
   echo '  '
	echo CREATING FUNCTION $SKILL_NM
   echo ' '
   create_function
   add_trigger
else
	echo UPDATING FUNCTION $SKILL_NM
fi

